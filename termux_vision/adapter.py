"""
termux_vision.adapter
======================
AMEVA Component Protocol v1 — Orchestrator Adapter (v0.8.1 호환)
"""
from __future__ import annotations

from typing import Any, AsyncIterator

from ameva_component.adapter_base import BaseOrchestratorAdapter
from termux_vision.control.component import VisionControl


class VisionOrchestratorAdapter(BaseOrchestratorAdapter):
    """Vision Orchestrator Adapter.

    이미지 분석 / VLM captioning은 파일 기반으로 수행됩니다.
    infer()는 image_path를 받아 분석 결과를 반환합니다.
    Native backend 실패 시 fallback_used=True를 명시합니다.
    """

    COMPONENT_ID = "termux-vision"

    def __init__(self, control: VisionControl | None = None) -> None:
        self._control = control or VisionControl()

    async def infer(self, request: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        """Vision inference: image_path → analysis result.

        request 키:
            image_path (str): 분석할 이미지 파일 경로 (필수)
            task (str): 작업 유형 — "caption" | "vlm" | "detect" (선택, 기본: "caption")
            prompt (str): VLM 프롬프트 (task="vlm"일 때 사용)
            model_id (str): 모델 ID (선택)

        반환 프레임:
            {"type": "vision_result", "task": str, "result": dict, "fallback_used": bool}
            {"type": "error", "code": str, "message": str}
        """
        image_path = request.get("image_path", "").strip()
        if not image_path:
            yield {
                "type": "error",
                "ok": False,
                "error": {
                    "code": "IMAGE_PATH_MISSING",
                    "message": "image_path is required for Vision infer",
                    "operation": "infer",
                    "component_id": self.COMPONENT_ID,
                    "retryable": False,
                },
            }
            return

        if hasattr(self._control, "analyze"):
            try:
                result = await self._control.analyze(request)
                yield {
                    "type": "vision_result",
                    "task": request.get("task", "caption"),
                    "result": result.get("result", {}),
                    "fallback_used": result.get("fallback_used", False),
                    "requested_backend": result.get("requested_backend"),
                    "executed_backend": result.get("executed_backend"),
                    "ok": True,
                }
            except Exception as exc:
                yield {
                    "type": "error",
                    "ok": False,
                    "error": {
                        "code": "VISION_INFERENCE_FAILED",
                        "message": str(exc),
                        "operation": "infer",
                        "component_id": self.COMPONENT_ID,
                        "retryable": True,
                    },
                }
        else:
            yield self._not_supported("infer.analyze")


def create_adapter() -> VisionOrchestratorAdapter:
    """Entry Point Factory."""
    return VisionOrchestratorAdapter()
