#!/usr/bin/env node

/**
 * termux-vision: Node.js Global CLI Binary.
 * High-performance on-device Computer Vision & VLM Multimodal Framework.
 * Open-Source under Apache License 2.0.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');

const { version } = require('../package.json');
const { runDoctor } = require('../lib/doctor');
const { ModelCacheManager, CATALOG } = require('../lib/cache');
const { load } = require('../lib/vlm');
const { canny } = require('../lib/cv');
const {
  ModelNotFoundError,
  NoInstalledModelsError,
  ModelSelectionRequiredError,
  VulkanNotAvailableError,
  RuntimeNotFoundError,
  ModelDownloadError
} = require('../lib/errors');

const args = process.argv.slice(2);
const command = args[0] || '--help';

function getArg(flag, alias = null) {
  let idx = args.indexOf(flag);
  if (idx === -1 && alias) idx = args.indexOf(alias);
  return idx !== -1 && args[idx + 1] ? args[idx + 1] : null;
}

function hasFlag(flag, alias = null) {
  return args.includes(flag) || (alias && args.includes(alias));
}

function printHelp() {
  console.log(`termux-vision CLI v${version} (Node.js Engine)`);
  console.log('Usage: termux-vision <command> [options]\n');
  console.log('Commands:');
  console.log('  doctor                           Inspect device hardware, RAM, and Vulkan GPU');
  console.log('  model list                       List installed VLM models');
  console.log('  model install <model_id>         Download and install official VLM model');
  console.log('  model download <url_or_repo>     Freely download model from Hugging Face or direct URL');
  console.log('  model remove <model_id>          Remove model from cache');
  console.log('  vlm <image_path> [options]       Execute multimodal image description/chat');
  console.log('  canny <image_path> [options]     Run Canny edge detection');
  console.log('  benchmark                        Run on-device vision latency benchmark\n');
  console.log('Options for VLM:');
  console.log('  -p, --prompt <text>              Prompt query');
  console.log('  -m, --model <model_id_or_path>   Model ID or direct path to .gguf file');
  console.log('  --mmproj <path>                  Vision projector path (mmproj-*.gguf)');
  console.log('  --device <auto|cpu|vulkan|gpu>   Device backend (auto: Vulkan with CPU fallback; gpu: strict Vulkan)');
  console.log('  --runtime <path>                 Explicit path to llama-cli executable');
  console.log('  --allow-download                 Automatically download model if missing');
  console.log('  -t, --threads <num>              Inference threads (default: 4)');
  console.log('  -n, --max-tokens <num>           Maximum generated tokens (default: 150)');
  console.log('  --temp, --temperature <val>      Sampling temperature (default: 0.2)');
  console.log('  --top-p <val>                    Top-p nucleus sampling');
  console.log('  --top-k <num>                    Top-k sampling threshold');
  console.log('  --repeat-penalty <val>           Repetition penalty (default: 1.2)');
  console.log('  --seed <num>                     Random RNG seed');
  console.log('  --system-prompt <text>           System prompt context');
  console.log('  --ngl <num>                      Number of GPU offload layers');
  console.log('  --json                           Output full metrics in JSON format');
}

async function promptUser(question) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stderr });
  return new Promise((resolve) => {
    rl.question(question, (ans) => {
      rl.close();
      resolve(ans.trim().toLowerCase());
    });
  });
}

async function main() {
  if (hasFlag('-v') || hasFlag('--version')) {
    console.log(`termux-vision ${version}`);
    process.exit(0);
  }

  if (command === '--help' || command === '-h' || command === 'help') {
    printHelp();
    process.exit(0);
  }

  const cache = new ModelCacheManager();

  if (command === 'doctor') {
    const probeVulkan = hasFlag('--probe-vulkan');
    const isJson = hasFlag('--json');
    const rep = runDoctor(probeVulkan);

    if (isJson) {
      console.log(JSON.stringify(rep, null, 2));
    } else {
      console.log('=== termux-vision Diagnostic Doctor (Node.js Engine) ===');
      console.log(`  Platform : ${rep.platform.system} (${rep.platform.machine}) | Android: ${rep.platform.isAndroid}`);
      console.log(`  RAM      : Total ${rep.hardware.totalRamMb}MB | Available ${rep.hardware.availableRamMb}MB`);
      console.log(`  CPU Cores: ${rep.hardware.cpuCores}`);
      console.log(`  Vulkan   : Loader=${rep.vulkan.loaderDetected} | Driver=${rep.vulkan.driverDetected} | Status=${rep.vulkan.status}`);
      console.log(`  Models   : ${rep.vlmRuntime.installedModelsCount} installed in ${rep.vlmRuntime.cacheDir}`);
      console.log(`  Preset   : ${rep.recommendedPreset}`);
    }
    process.exit(0);
  }

  if (command === 'model') {
    const action = args[1] || 'list';
    if (action === 'list') {
      const isJson = hasFlag('--json');
      const installed = cache.listInstalled();
      if (isJson) {
        console.log(JSON.stringify(installed, null, 2));
      } else {
        console.log(`=== Installed VLM Models (${installed.length}) ===`);
        if (installed.length === 0) {
          console.log('  (none in ~/.cache/termux-vision/models)');
        } else {
          for (const m of installed) {
            console.log(`  - ${m.modelId.padEnd(20)} | Tier: ${m.tier} | State: ${m.state} | Size: ${m.sizeMb}MB`);
          }
        }
        console.log('\nAvailable Official Presets:');
        for (const [k, v] of Object.entries(CATALOG)) {
          console.log(`  * ${k.padEnd(20)} | Tier: ${v.tier} | Est. RAM: ${v.estimatedMemoryMb}MB`);
        }
      }
      process.exit(0);
    }

    if (action === 'install') {
      const modelId = args[2];
      if (!modelId) {
        console.error('[ERROR] Please specify a model ID to install (e.g. smolvlm-500m-q4).');
        process.exit(2);
      }
      console.log(`[*] Installing model: ${modelId}...`);
      try {
        await cache.install(modelId, (fname, downloaded, total) => {
          const pct = total > 0 ? (downloaded / total * 100).toFixed(1) : '0.0';
          process.stdout.write(`\r  Downloading ${fname}: ${(downloaded / 1048576).toFixed(1)}/${(total / 1048576).toFixed(1)}MB (${pct}%)`);
        });
        console.log(`\n[+] Successfully installed '${modelId}'.`);
        process.exit(0);
      } catch (err) {
        console.error(`\n[-] Model installation failed: ${err.message}`);
        process.exit(11);
      }
    }

    if (action === 'download') {
      const source = args[2];
      if (!source) {
        console.error('[ERROR] Please provide a Hugging Face repo or direct URL.');
        process.exit(2);
      }
      const outDir = getArg('-o', '--output') || cache.modelsDir;
      console.log(`[*] Downloading model from: ${source}...`);
      try {
        let dest = path.join(outDir, path.basename(source.split('?')[0]));
        if (source.startsWith('hf:') || source.includes(':')) {
          const parts = (source.startsWith('hf:') ? source.slice(3) : source).split(':');
          if (parts.length === 2) {
            const url = `https://huggingface.co/${parts[0].trim()}/resolve/main/${parts[1].trim()}`;
            dest = path.join(outDir, parts[1].trim());
            await cache.downloadFile(url, dest, (fname, d, t) => {
              const pct = t > 0 ? (d / t * 100).toFixed(1) : '0.0';
              process.stdout.write(`\r  Downloading ${fname}: ${(d / 1048576).toFixed(1)}/${(t / 1048576).toFixed(1)}MB (${pct}%)`);
            });
          }
        } else if (source.startsWith('http')) {
          await cache.downloadFile(source, dest, (fname, d, t) => {
            const pct = t > 0 ? (d / t * 100).toFixed(1) : '0.0';
            process.stdout.write(`\r  Downloading ${fname}: ${(d / 1048576).toFixed(1)}/${(t / 1048576).toFixed(1)}MB (${pct}%)`);
          });
        }
        console.log(`\n[+] Model downloaded successfully to: ${dest}`);
        process.exit(0);
      } catch (err) {
        console.error(`\n[-] Model download failed: ${err.message}`);
        process.exit(11);
      }
    }

    if (action === 'remove') {
      const modelId = args[2];
      if (!modelId) {
        console.error('[ERROR] Please specify a model ID to remove.');
        process.exit(2);
      }
      if (cache.remove(modelId)) {
        console.log(`[+] Model '${modelId}' removed from cache.`);
        process.exit(0);
      } else {
        console.error(`[-] Model '${modelId}' was not found in cache.`);
        process.exit(10);
      }
    }
  }

  if (command === 'vlm') {
    const imagePath = args[1];
    if (!imagePath || imagePath.startsWith('-')) {
      console.error('[ERROR] Missing input image path for VLM inference.');
      console.error('Usage: termux-vision vlm <image_path> [options]');
      process.exit(2);
    }

    const prompt = getArg('-p', '--prompt');
    const model = getArg('-m', '--model');
    const mmproj = getArg('--mmproj', null);
    const device = getArg('--device', null) || 'auto';
    const runtime = getArg('--runtime', null);
    const allowDownload = hasFlag('--allow-download');
    const threads = getArg('-t', '--threads');
    const maxTokens = getArg('-n', '--max-tokens');
    const temp = getArg('--temp', '--temperature');
    const topP = getArg('--top-p', null);
    const topK = getArg('--top-k', null);
    const repeatPenalty = getArg('--repeat-penalty', null);
    const seed = getArg('--seed', null);
    const systemPrompt = getArg('--system-prompt', null);
    const ngl = getArg('--ngl', null);
    const isJson = hasFlag('--json');

    try {
      let targetModel = model;
      if (!targetModel) {
        const installed = cache.listInstalled();
        if (installed.length === 0) {
          if (allowDownload) {
            targetModel = 'smolvlm-500m-q4';
          } else if (process.stdin.isTTY) {
            console.error('\n---------------------------------------------------------');
            console.error('  [Notice] No local VLM model is currently installed.');
            console.error('  Default Model : smolvlm-500m-q4 (SmolVLM 500M Instruct)');
            console.error('  Download Size : ~550 MB');
            console.error('  Target Path   : ~/.cache/termux-vision/models/smolvlm-500m-q4/');
            console.error('---------------------------------------------------------');
            const ans = await promptUser('Do you want to download and install this model now? [y/N]: ');
            if (ans === 'y' || ans === 'yes') {
              console.error('[*] Downloading smolvlm-500m-q4 (~550MB)...');
              await cache.install('smolvlm-500m-q4');
              console.error('[+] Successfully installed smolvlm-500m-q4.');
              targetModel = 'smolvlm-500m-q4';
            } else {
              throw new NoInstalledModelsError(cache.getAvailableCatalogModels());
            }
          } else {
            throw new NoInstalledModelsError(cache.getAvailableCatalogModels());
          }
        } else if (installed.length === 1) {
          targetModel = installed[0].modelId;
          console.error(`[INFO] Selected installed model: ${targetModel}`);
        } else {
          throw new ModelSelectionRequiredError(installed.map(m => m.modelId));
        }
      }

      const engine = await load({
        modelId: targetModel,
        mmprojPath: mmproj,
        device: device,
        runtimePath: runtime,
        allowDownload: allowDownload,
        threads: threads ? parseInt(threads, 10) : 4,
        ngl: ngl ? parseInt(ngl, 10) : null
      });

      const res = await engine.describe(imagePath, {
        prompt: prompt,
        maxTokens: maxTokens ? parseInt(maxTokens, 10) : 150,
        temperature: temp ? parseFloat(temp) : 0.2,
        topP: topP ? parseFloat(topP) : undefined,
        topK: topK ? parseInt(topK, 10) : undefined,
        repeatPenalty: repeatPenalty ? parseFloat(repeatPenalty) : undefined,
        seed: seed ? parseInt(seed, 10) : undefined,
        systemPrompt: systemPrompt || undefined
      });

      if (isJson) {
        console.log(JSON.stringify(res, null, 2));
      } else {
        if (res.warnings && res.warnings.length > 0) {
          for (const w of res.warnings) {
            console.error(`[WARNING] ${w}`);
          }
        }
        const tpsStr = res.metrics.tokensPerSecond ? ` | ${res.metrics.tokensPerSecond.toFixed(1)} t/s` : '';
        console.log(`\n[VLM Result | backend=${res.metrics.backend}${tpsStr}]`);
        console.log(res.text);
      }
      process.exit(0);
    } catch (err) {
      if (err instanceof VulkanNotAvailableError) {
        console.error(`[ERROR] ${err.message}`);
        process.exit(24);
      } else if (err instanceof RuntimeNotFoundError) {
        console.error(`[ERROR] ${err.message}`);
        process.exit(20);
      } else if (err instanceof NoInstalledModelsError) {
        console.error(`[ERROR] ${err.message}`);
        process.exit(21);
      } else if (err instanceof ModelSelectionRequiredError) {
        console.error(`[ERROR] ${err.message}`);
        process.exit(23);
      } else if (err instanceof ModelNotFoundError) {
        console.error(`[ERROR] ${err.message}`);
        process.exit(10);
      } else if (err instanceof ModelDownloadError) {
        console.error(`[ERROR] ${err.message}`);
        process.exit(11);
      } else {
        console.error(`[ERROR] VLM execution failed: ${err.message}`);
        process.exit(15);
      }
    }
  }

  if (command === 'benchmark') {
    console.log('=== termux-vision On-Device Benchmark (Node.js Engine) ===');
    const width = 256;
    const height = 256;
    const dummy = new Uint8Array(width * height);
    for (let i = 0; i < dummy.length; i++) dummy[i] = Math.floor(Math.random() * 256);

    const t0 = Date.now();
    const edges = canny(dummy, width, height, 40, 120);
    const lat = Date.now() - t0;
    console.log(`  - Canny Edge Detection (256x256): ${lat} ms`);
    console.log('[+] Benchmark Complete.');
    process.exit(0);
  }

  console.error(`[ERROR] Unknown command: '${command}'`);
  printHelp();
  process.exit(2);
}

main().catch((err) => {
  console.error(`[FATAL] ${err.message}`);
  process.exit(1);
});
