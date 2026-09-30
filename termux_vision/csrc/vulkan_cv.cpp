#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <vulkan/vulkan.h>
#include <mutex>
#include <vector>

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT __attribute__((visibility("default")))
#endif

// Embed precompiled SPIR-V bytecodes
static const uint32_t spv_sobel[] =
#include "sobel.spv.h"
;

static const uint32_t spv_nms[] =
#include "nms.spv.h"
;

static const uint32_t spv_hysteresis[] =
#include "hysteresis.spv.h"
;

// Vulkan Global State
struct VulkanCVContext {
    VkInstance instance;
    VkPhysicalDevice physical_device;
    VkPhysicalDeviceProperties props;
    VkDevice device;
    uint32_t queue_family_index;
    VkQueue queue;
    VkCommandPool command_pool;
    VkCommandBuffer cmd_buffer;
    VkFence fence;

    // Descriptors and Pipelines
    VkDescriptorPool descriptor_pool;
    
    VkDescriptorSetLayout desc_layout_sobel;
    VkPipelineLayout pipe_layout_sobel;
    VkPipeline pipe_sobel;
    VkDescriptorSet desc_set_sobel;

    VkDescriptorSetLayout desc_layout_nms;
    VkPipelineLayout pipe_layout_nms;
    VkPipeline pipe_nms;
    VkDescriptorSet desc_set_nms;

    VkDescriptorSetLayout desc_layout_hysteresis;
    VkPipelineLayout pipe_layout_hysteresis;
    VkPipeline pipe_hysteresis;
    VkDescriptorSet desc_set_hysteresis;

    // Buffers
    size_t current_capacity;
    VkBuffer buf_in;
    VkDeviceMemory mem_in;
    void* ptr_in;

    VkBuffer buf_mag;
    VkDeviceMemory mem_mag;

    VkBuffer buf_dir;
    VkDeviceMemory mem_dir;

    VkBuffer buf_edge;
    VkDeviceMemory mem_edge;

    VkBuffer buf_out;
    VkDeviceMemory mem_out;
    void* ptr_out;

    bool initialized;

    VulkanCVContext() {
        memset(this, 0, sizeof(VulkanCVContext));
    }
};

static VulkanCVContext g_vk;
static std::mutex g_vk_mutex;

static uint32_t find_memory_type(uint32_t type_filter, VkMemoryPropertyFlags properties) {
    VkPhysicalDeviceMemoryProperties mem_props;
    vkGetPhysicalDeviceMemoryProperties(g_vk.physical_device, &mem_props);
    for (uint32_t i = 0; i < mem_props.memoryTypeCount; i++) {
        if ((type_filter & (1 << i)) && (mem_props.memoryTypes[i].propertyFlags & properties) == properties) {
            return i;
        }
    }
    return 0xFFFFFFFF;
}

static VkShaderModule create_shader_module(const uint32_t* code, size_t code_bytes) {
    VkShaderModuleCreateInfo create_info = {VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
    create_info.codeSize = code_bytes;
    create_info.pCode = code;
    VkShaderModule module;
    if (vkCreateShaderModule(g_vk.device, &create_info, NULL, &module) != VK_SUCCESS) {
        return VK_NULL_HANDLE;
    }
    return module;
}

static int create_buffer(
    VkDeviceSize size, 
    VkBufferUsageFlags usage, 
    VkMemoryPropertyFlags properties, 
    VkBuffer* buffer, 
    VkDeviceMemory* memory, 
    void** mapped_ptr = NULL
) {
    VkBufferCreateInfo buf_info = {VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
    buf_info.size = size;
    buf_info.usage = usage;
    buf_info.sharingMode = VK_SHARING_MODE_EXCLUSIVE;

    if (vkCreateBuffer(g_vk.device, &buf_info, NULL, buffer) != VK_SUCCESS) {
        return 0;
    }

    VkMemoryRequirements mem_reqs;
    vkGetBufferMemoryRequirements(g_vk.device, *buffer, &mem_reqs);

    VkMemoryAllocateInfo alloc_info = {VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
    alloc_info.allocationSize = mem_reqs.size;
    alloc_info.memoryTypeIndex = find_memory_type(mem_reqs.memoryTypeBits, properties);
    if (alloc_info.memoryTypeIndex == 0xFFFFFFFF) {
        return 0;
    }

    if (vkAllocateMemory(g_vk.device, &alloc_info, NULL, memory) != VK_SUCCESS) {
        return 0;
    }

    if (vkBindBufferMemory(g_vk.device, *buffer, *memory, 0) != VK_SUCCESS) {
        return 0;
    }

    if (mapped_ptr) {
        if (vkMapMemory(g_vk.device, *memory, 0, size, 0, mapped_ptr) != VK_SUCCESS) {
            return 0;
        }
    }
    return 1;
}

static void destroy_buffers() {
    if (g_vk.mem_in) {
        if (g_vk.ptr_in) vkUnmapMemory(g_vk.device, g_vk.mem_in);
        vkFreeMemory(g_vk.device, g_vk.mem_in, NULL);
        vkDestroyBuffer(g_vk.device, g_vk.buf_in, NULL);
    }
    if (g_vk.mem_mag) {
        vkFreeMemory(g_vk.device, g_vk.mem_mag, NULL);
        vkDestroyBuffer(g_vk.device, g_vk.buf_mag, NULL);
    }
    if (g_vk.mem_dir) {
        vkFreeMemory(g_vk.device, g_vk.mem_dir, NULL);
        vkDestroyBuffer(g_vk.device, g_vk.buf_dir, NULL);
    }
    if (g_vk.mem_edge) {
        vkFreeMemory(g_vk.device, g_vk.mem_edge, NULL);
        vkDestroyBuffer(g_vk.device, g_vk.buf_edge, NULL);
    }
    if (g_vk.mem_out) {
        if (g_vk.ptr_out) vkUnmapMemory(g_vk.device, g_vk.mem_out);
        vkFreeMemory(g_vk.device, g_vk.mem_out, NULL);
        vkDestroyBuffer(g_vk.device, g_vk.buf_out, NULL);
    }
    g_vk.ptr_in = NULL;
    g_vk.ptr_out = NULL;
    g_vk.current_capacity = 0;
}

static int ensure_buffers(size_t total_px) {
    if (g_vk.current_capacity >= total_px && g_vk.buf_in && g_vk.buf_out) {
        return 1;
    }

    destroy_buffers();

    VkMemoryPropertyFlags host_flags = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT;
    VkMemoryPropertyFlags dev_flags = VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT;

    // Buffer In (uint8_t)
    if (!create_buffer(total_px, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, host_flags, &g_vk.buf_in, &g_vk.mem_in, &g_vk.ptr_in)) {
        return 0;
    }

    // Buffer Mag (float)
    if (!create_buffer(total_px * sizeof(float), VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, dev_flags | host_flags, &g_vk.buf_mag, &g_vk.mem_mag)) {
        return 0;
    }

    // Buffer Dir (uint8_t)
    if (!create_buffer(total_px, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, dev_flags | host_flags, &g_vk.buf_dir, &g_vk.mem_dir)) {
        return 0;
    }

    // Buffer Edge (uint8_t)
    if (!create_buffer(total_px, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, dev_flags | host_flags, &g_vk.buf_edge, &g_vk.mem_edge)) {
        return 0;
    }

    // Buffer Out (uint8_t)
    if (!create_buffer(total_px, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT, host_flags, &g_vk.buf_out, &g_vk.mem_out, &g_vk.ptr_out)) {
        return 0;
    }

    // Update Descriptor Sets
    VkDescriptorBufferInfo b_in = {g_vk.buf_in, 0, total_px};
    VkDescriptorBufferInfo b_mag = {g_vk.buf_mag, 0, total_px * sizeof(float)};
    VkDescriptorBufferInfo b_dir = {g_vk.buf_dir, 0, total_px};
    VkDescriptorBufferInfo b_edge = {g_vk.buf_edge, 0, total_px};
    VkDescriptorBufferInfo b_out = {g_vk.buf_out, 0, total_px};

    // Sobel Descriptors (0: In, 1: Mag, 2: Dir)
    VkWriteDescriptorSet writes_sobel[3] = {};
    for (int i = 0; i < 3; i++) {
        writes_sobel[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes_sobel[i].dstSet = g_vk.desc_set_sobel;
        writes_sobel[i].dstBinding = i;
        writes_sobel[i].descriptorCount = 1;
        writes_sobel[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    }
    writes_sobel[0].pBufferInfo = &b_in;
    writes_sobel[1].pBufferInfo = &b_mag;
    writes_sobel[2].pBufferInfo = &b_dir;
    vkUpdateDescriptorSets(g_vk.device, 3, writes_sobel, 0, NULL);

    // NMS Descriptors (0: Mag, 1: Dir, 2: Edge)
    VkWriteDescriptorSet writes_nms[3] = {};
    for (int i = 0; i < 3; i++) {
        writes_nms[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes_nms[i].dstSet = g_vk.desc_set_nms;
        writes_nms[i].dstBinding = i;
        writes_nms[i].descriptorCount = 1;
        writes_nms[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    }
    writes_nms[0].pBufferInfo = &b_mag;
    writes_nms[1].pBufferInfo = &b_dir;
    writes_nms[2].pBufferInfo = &b_edge;
    vkUpdateDescriptorSets(g_vk.device, 3, writes_nms, 0, NULL);

    // Hysteresis Descriptors (0: Edge, 1: Out)
    VkWriteDescriptorSet writes_hyst[2] = {};
    for (int i = 0; i < 2; i++) {
        writes_hyst[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes_hyst[i].dstSet = g_vk.desc_set_hysteresis;
        writes_hyst[i].dstBinding = i;
        writes_hyst[i].descriptorCount = 1;
        writes_hyst[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    }
    writes_hyst[0].pBufferInfo = &b_edge;
    writes_hyst[1].pBufferInfo = &b_out;
    vkUpdateDescriptorSets(g_vk.device, 2, writes_hyst, 0, NULL);

    g_vk.current_capacity = total_px;
    return 1;
}

static int init_vulkan_context() {
    if (g_vk.initialized) return 1;

    VkApplicationInfo app_info = {VK_STRUCTURE_TYPE_APPLICATION_INFO};
    app_info.pApplicationName = "termux_vision_vulkan";
    app_info.applicationVersion = VK_MAKE_VERSION(1, 0, 0);
    app_info.pEngineName = "AMEVA";
    app_info.engineVersion = VK_MAKE_VERSION(1, 0, 0);
    app_info.apiVersion = VK_API_VERSION_1_2;

    VkInstanceCreateInfo inst_info = {VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
    inst_info.pApplicationInfo = &app_info;

    if (vkCreateInstance(&inst_info, NULL, &g_vk.instance) != VK_SUCCESS) {
        return 0;
    }

    uint32_t dev_count = 0;
    vkEnumeratePhysicalDevices(g_vk.instance, &dev_count, NULL);
    if (dev_count == 0) {
        vkDestroyInstance(g_vk.instance, NULL);
        return 0;
    }

    std::vector<VkPhysicalDevice> devs(dev_count);
    vkEnumeratePhysicalDevices(g_vk.instance, &dev_count, devs.data());
    g_vk.physical_device = devs[0];
    vkGetPhysicalDeviceProperties(g_vk.physical_device, &g_vk.props);

    // Find compute queue
    uint32_t queue_prop_count = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(g_vk.physical_device, &queue_prop_count, NULL);
    std::vector<VkQueueFamilyProperties> queue_props(queue_prop_count);
    vkGetPhysicalDeviceQueueFamilyProperties(g_vk.physical_device, &queue_prop_count, queue_props.data());

    int compute_idx = -1;
    for (uint32_t i = 0; i < queue_prop_count; i++) {
        if (queue_props[i].queueFlags & VK_QUEUE_COMPUTE_BIT) {
            compute_idx = (int)i;
            break;
        }
    }
    if (compute_idx < 0) {
        vkDestroyInstance(g_vk.instance, NULL);
        return 0;
    }
    g_vk.queue_family_index = (uint32_t)compute_idx;

    // Enable 8-bit storage feature
    VkPhysicalDevice8BitStorageFeaturesKHR feat8 = {VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_8BIT_STORAGE_FEATURES_KHR};
    feat8.storageBuffer8BitAccess = VK_TRUE;

    float prio = 1.0f;
    VkDeviceQueueCreateInfo q_info = {VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
    q_info.queueFamilyIndex = g_vk.queue_family_index;
    q_info.queueCount = 1;
    q_info.pQueuePriorities = &prio;

    const char* ext_names[] = {
        VK_KHR_STORAGE_BUFFER_STORAGE_CLASS_EXTENSION_NAME,
        VK_KHR_8BIT_STORAGE_EXTENSION_NAME
    };

    VkDeviceCreateInfo dev_info = {VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
    dev_info.pNext = &feat8;
    dev_info.queueCreateInfoCount = 1;
    dev_info.pQueueCreateInfos = &q_info;
    dev_info.enabledExtensionCount = 2;
    dev_info.ppEnabledExtensionNames = ext_names;

    if (vkCreateDevice(g_vk.physical_device, &dev_info, NULL, &g_vk.device) != VK_SUCCESS) {
        // Fallback without explicit 8-bit extension if core 1.2 already enables it
        dev_info.enabledExtensionCount = 0;
        dev_info.ppEnabledExtensionNames = NULL;
        if (vkCreateDevice(g_vk.physical_device, &dev_info, NULL, &g_vk.device) != VK_SUCCESS) {
            vkDestroyInstance(g_vk.instance, NULL);
            return 0;
        }
    }

    vkGetDeviceQueue(g_vk.device, g_vk.queue_family_index, 0, &g_vk.queue);

    // Command Pool & Buffer & Fence
    VkCommandPoolCreateInfo cp_info = {VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
    cp_info.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    cp_info.queueFamilyIndex = g_vk.queue_family_index;
    vkCreateCommandPool(g_vk.device, &cp_info, NULL, &g_vk.command_pool);

    VkCommandBufferAllocateInfo cb_info = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
    cb_info.commandPool = g_vk.command_pool;
    cb_info.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    cb_info.commandBufferCount = 1;
    vkAllocateCommandBuffers(g_vk.device, &cb_info, &g_vk.cmd_buffer);

    VkFenceCreateInfo fence_info = {VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
    vkCreateFence(g_vk.device, &fence_info, NULL, &g_vk.fence);

    // Descriptor Pool
    VkDescriptorPoolSize pool_sizes[1] = {
        {VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 16}
    };
    VkDescriptorPoolCreateInfo dp_info = {VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
    dp_info.maxSets = 8;
    dp_info.poolSizeCount = 1;
    dp_info.pPoolSizes = pool_sizes;
    vkCreateDescriptorPool(g_vk.device, &dp_info, NULL, &g_vk.descriptor_pool);

    // Pipelines Creation Helper lambda
    auto make_pipe = [](
        const uint32_t* spv_code, 
        size_t spv_bytes, 
        int num_bindings, 
        size_t push_const_size,
        VkDescriptorSetLayout* out_layout,
        VkPipelineLayout* out_pipe_layout,
        VkPipeline* out_pipe,
        VkDescriptorSet* out_set
    ) -> bool {
        std::vector<VkDescriptorSetLayoutBinding> bindings(num_bindings);
        for (int i = 0; i < num_bindings; i++) {
            bindings[i].binding = i;
            bindings[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
            bindings[i].descriptorCount = 1;
            bindings[i].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
        }

        VkDescriptorSetLayoutCreateInfo dsl_info = {VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
        dsl_info.bindingCount = (uint32_t)bindings.size();
        dsl_info.pBindings = bindings.data();
        if (vkCreateDescriptorSetLayout(g_vk.device, &dsl_info, NULL, out_layout) != VK_SUCCESS) return false;

        VkPushConstantRange pc_range = {};
        pc_range.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
        pc_range.offset = 0;
        pc_range.size = (uint32_t)push_const_size;

        VkPipelineLayoutCreateInfo pl_info = {VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
        pl_info.setLayoutCount = 1;
        pl_info.pSetLayouts = out_layout;
        pl_info.pushConstantRangeCount = 1;
        pl_info.pPushConstantRanges = &pc_range;
        if (vkCreatePipelineLayout(g_vk.device, &pl_info, NULL, out_pipe_layout) != VK_SUCCESS) return false;

        VkShaderModule module = create_shader_module(spv_code, spv_bytes);
        if (!module) return false;

        VkComputePipelineCreateInfo cp_info = {VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};
        cp_info.stage.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        cp_info.stage.stage = VK_SHADER_STAGE_COMPUTE_BIT;
        cp_info.stage.module = module;
        cp_info.stage.pName = "main";
        cp_info.layout = *out_pipe_layout;

        VkResult res = vkCreateComputePipelines(g_vk.device, VK_NULL_HANDLE, 1, &cp_info, NULL, out_pipe);
        vkDestroyShaderModule(g_vk.device, module, NULL);
        if (res != VK_SUCCESS) return false;

        VkDescriptorSetAllocateInfo ds_alloc = {VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
        ds_alloc.descriptorPool = g_vk.descriptor_pool;
        ds_alloc.descriptorSetCount = 1;
        ds_alloc.pSetLayouts = out_layout;
        if (vkAllocateDescriptorSets(g_vk.device, &ds_alloc, out_set) != VK_SUCCESS) return false;

        return true;
    };

    // 1. Sobel Pipeline
    if (!make_pipe(spv_sobel, sizeof(spv_sobel), 3, 2 * sizeof(int),
                   &g_vk.desc_layout_sobel, &g_vk.pipe_layout_sobel, &g_vk.pipe_sobel, &g_vk.desc_set_sobel)) {
        return 0;
    }

    // 2. NMS Pipeline
    struct NmsPush { int w, h; float low, high; };
    if (!make_pipe(spv_nms, sizeof(spv_nms), 3, sizeof(NmsPush),
                   &g_vk.desc_layout_nms, &g_vk.pipe_layout_nms, &g_vk.pipe_nms, &g_vk.desc_set_nms)) {
        return 0;
    }

    // 3. Hysteresis Pipeline
    if (!make_pipe(spv_hysteresis, sizeof(spv_hysteresis), 2, 2 * sizeof(int),
                   &g_vk.desc_layout_hysteresis, &g_vk.pipe_layout_hysteresis, &g_vk.pipe_hysteresis, &g_vk.desc_set_hysteresis)) {
        return 0;
    }

    g_vk.initialized = true;
    return 1;
}

extern "C" {

EXPORT int is_vulkan_cv_available() {
    std::lock_guard<std::mutex> lock(g_vk_mutex);
    return init_vulkan_context();
}

EXPORT const char* get_vulkan_device_name() {
    std::lock_guard<std::mutex> lock(g_vk_mutex);
    if (!init_vulkan_context()) return "Unknown Vulkan Device";
    return g_vk.props.deviceName;
}

// 100% Vulkan GPU Compute Canny Edge Detector (Zero-CPU Fallback)
EXPORT int vulkan_canny(
    const unsigned char* src, 
    unsigned char* dst, 
    int width, 
    int height, 
    float low_thresh, 
    float high_thresh
) {
    if (!src || !dst || width <= 0 || height <= 0) return 0;

    std::lock_guard<std::mutex> lock(g_vk_mutex);
    if (!init_vulkan_context()) return 0;

    size_t total_px = (size_t)width * (size_t)height;
    if (!ensure_buffers(total_px)) return 0;

    // 1. Upload input image directly to Host-Visible & Coherent VkBuffer
    memcpy(g_vk.ptr_in, src, total_px);

    // 2. Record End-to-End GPU Compute Command Buffer
    vkResetFences(g_vk.device, 1, &g_vk.fence);
    vkResetCommandBuffer(g_vk.cmd_buffer, 0);

    VkCommandBufferBeginInfo begin_info = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    begin_info.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    vkBeginCommandBuffer(g_vk.cmd_buffer, &begin_info);

    uint32_t groups_x = ((uint32_t)width + 15) / 16;
    uint32_t groups_y = ((uint32_t)height + 15) / 16;

    // ── Pass 1: Sobel Gradient & Angle ──
    vkCmdBindPipeline(g_vk.cmd_buffer, VK_PIPELINE_BIND_POINT_COMPUTE, g_vk.pipe_sobel);
    vkCmdBindDescriptorSets(g_vk.cmd_buffer, VK_PIPELINE_BIND_POINT_COMPUTE, g_vk.pipe_layout_sobel, 0, 1, &g_vk.desc_set_sobel, 0, NULL);
    int sobel_push[2] = {width, height};
    vkCmdPushConstants(g_vk.cmd_buffer, g_vk.pipe_layout_sobel, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof(sobel_push), sobel_push);
    vkCmdDispatch(g_vk.cmd_buffer, groups_x, groups_y, 1);

    // Memory Barrier: Sobel Write -> NMS Read
    VkMemoryBarrier mem_bar1 = {VK_STRUCTURE_TYPE_MEMORY_BARRIER};
    mem_bar1.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
    mem_bar1.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
    vkCmdPipelineBarrier(g_vk.cmd_buffer, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         0, 1, &mem_bar1, 0, NULL, 0, NULL);

    // ── Pass 2: NMS & Double Thresholding ──
    vkCmdBindPipeline(g_vk.cmd_buffer, VK_PIPELINE_BIND_POINT_COMPUTE, g_vk.pipe_nms);
    vkCmdBindDescriptorSets(g_vk.cmd_buffer, VK_PIPELINE_BIND_POINT_COMPUTE, g_vk.pipe_layout_nms, 0, 1, &g_vk.desc_set_nms, 0, NULL);
    struct NmsPush { int w, h; float low, high; } nms_push = {width, height, low_thresh, high_thresh};
    vkCmdPushConstants(g_vk.cmd_buffer, g_vk.pipe_layout_nms, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof(nms_push), &nms_push);
    vkCmdDispatch(g_vk.cmd_buffer, groups_x, groups_y, 1);

    // Memory Barrier: NMS Write -> Hysteresis Read
    VkMemoryBarrier mem_bar2 = {VK_STRUCTURE_TYPE_MEMORY_BARRIER};
    mem_bar2.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
    mem_bar2.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
    vkCmdPipelineBarrier(g_vk.cmd_buffer, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                         0, 1, &mem_bar2, 0, NULL, 0, NULL);

    // ── Pass 3: 8-Connected Hysteresis Propagation ──
    vkCmdBindPipeline(g_vk.cmd_buffer, VK_PIPELINE_BIND_POINT_COMPUTE, g_vk.pipe_hysteresis);
    vkCmdBindDescriptorSets(g_vk.cmd_buffer, VK_PIPELINE_BIND_POINT_COMPUTE, g_vk.pipe_layout_hysteresis, 0, 1, &g_vk.desc_set_hysteresis, 0, NULL);
    int hyst_push[2] = {width, height};
    vkCmdPushConstants(g_vk.cmd_buffer, g_vk.pipe_layout_hysteresis, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof(hyst_push), hyst_push);
    vkCmdDispatch(g_vk.cmd_buffer, groups_x, groups_y, 1);

    // Memory Barrier: Hysteresis Write -> Host Read
    VkMemoryBarrier mem_bar3 = {VK_STRUCTURE_TYPE_MEMORY_BARRIER};
    mem_bar3.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
    mem_bar3.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
    vkCmdPipelineBarrier(g_vk.cmd_buffer, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_HOST_BIT,
                         0, 1, &mem_bar3, 0, NULL, 0, NULL);

    vkEndCommandBuffer(g_vk.cmd_buffer);

    // 3. Submit GPU Execution & Synchronize via Fence
    VkSubmitInfo submit_info = {VK_STRUCTURE_TYPE_SUBMIT_INFO};
    submit_info.commandBufferCount = 1;
    submit_info.pCommandBuffers = &g_vk.cmd_buffer;

    if (vkQueueSubmit(g_vk.queue, 1, &submit_info, g_vk.fence) != VK_SUCCESS) {
        return 0;
    }

    // Wait for GPU completion (100% on-device finish)
    if (vkWaitForFences(g_vk.device, 1, &g_vk.fence, VK_TRUE, 2000000000ULL) != VK_SUCCESS) {
        return 0;
    }

    // 4. Download final edge image directly from Host-Visible VkBuffer
    memcpy(dst, g_vk.ptr_out, total_px);
    return 1;
}

}
