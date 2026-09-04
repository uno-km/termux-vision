"""
termux_vision.adapter
======================
AMEVA Component Protocol v1 — Orchestrator Adapter (v0.8.1 호환)

P0-2: infer() fallback yield _not_supported → raise OperationNotSupported
P0-4: except Exception → retryable 분류, 원본 오류 코드 보존
"""
from __future__ import annotations

from typing import Any, AsyncIterator

from ameva_component.adapter_base import BaseOrchestratorAdapter
from ameva_component.exceptions import ComponentError, OperationNotSupported
from termux_vision.control.component import VisionControl


class VisionOrchestratorAdapter(BaseOrchestratorAdapter):
    """Vision Orchestrator Adapter.

    이미지 분석 / VLM captioning은 파일 기반으로 수행됩니다.
    infer(): image_path를 받아 분석 결과를 반환합니다.
    Native backend 실패 시 fallback_used=True를 명시합니다.
    """

    COMPONENT_ID = "termux-vision"

    _RETRYABLE_CODES: frozenset[str] = frozenset({
        "REMOTE_TIMEOUT",
        "MODEL_BUSY",
        "BACKEND_OVERLOADED",
    })
    _NON_RETRYABLE_CODES: frozenset[str] = frozenset({
        "IMAGE_PATH_FORBIDDEN",
        "IMAGE_FORMAT_UNSUPPORTED",
        "IMAGE_CORRUPT",
        "MODEL_NOT_FOUND",
        "HASH_MISMATCH",
    })

    def __init__(self, control: VisionControl | None = None) -> None:
        self._control = control or VisionControl()

    async def infer(self, request: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        """Vision inference: image_path → analysis result.

        request 키:
            image_path (str): 분석할 이미지 파일 경로 (필수)
            task (str): "caption" | "vlm" | "detect" (선택, 기본: "caption")
            prompt (str): VLM 프롬프트 (task="vlm"일 때)
            model_id (str): 모델 ID (선택)

        반환 프레임:
            {"type": "vision_result", "task": str, "result": dict, ...}
            {"type": "error", "ok": False, "error": {...}}
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

        if not hasattr(self._control, "analyze"):
            # P0-2: fallback yield → raise
            raise OperationNotSupported(operation="infer.analyze", component_id=self.COMPONENT_ID)

        try:
            result = await self._control.analyze(request)

            if not isinstance(result, dict):
                raise ValueError(f"analyze() must return dict, got {type(result).__name__}")

            if result.get("ok") is not True:
                err_payload = result.get("error") if isinstance(result.get("error"), dict) else {}
                yield {
                    "type": "error",
                    "ok": False,
                    "error": {
                        "code": err_payload.get("code", "ADAPTER_RESULT_NOT_SUCCESS"),
                        "message": err_payload.get("message", "analyze() did not return ok=True"),
                        "operation": "infer",
                        "component_id": self.COMPONENT_ID,
                        "retryable": False,
                        "details": {"result_keys": sorted(result.keys())},
                    },
                }
                return

            if "result" not in result:
                raise ValueError("analyze() result missing required field 'result'")

            yield {
                "type": "vision_result",
                "task": request.get("task", "caption"),
                "result": result["result"],
                "fallback_used": result.get("fallback_used", False),
                "requested_backend": result.get("requested_backend"),
                "executed_backend": result.get("executed_backend"),
                "ok": True,
            }

        except ComponentError as component_err:
            err_dict = component_err.to_dict() if hasattr(component_err, "to_dict") else {
                "code": getattr(component_err, "code", "COMPONENT_ERROR"),
                "message": str(component_err),
                "retryable": getattr(component_err, "retryable", False),
            }
            yield {
                "type": "error",
                "ok": False,
                "error": {
                    **err_dict,
                    "operation": "infer",
                    "component_id": self.COMPONENT_ID,
                    "retryable": self._classify_retryable(
                        err_dict.get("code", ""), default=err_dict.get("retryable", False)
                    ),
                },
            }

        except (ValueError, TypeError) as contract_err:
            yield {
                "type": "error",
                "ok": False,
                "error": {
                    "code": "ADAPTER_CONTRACT_ERROR",
                    "message": str(contract_err),
                    "operation": "infer",
                    "component_id": self.COMPONENT_ID,
                    "retryable": False,
                },
            }

        except Exception as unexpected_err:
            import logging
            logging.getLogger(__name__).exception("Vision adapter unexpected error during infer: %s", unexpected_err)
            code = getattr(unexpected_err, "code", "ADAPTER_INTERNAL_ERROR")
            yield {
                "type": "error",
                "ok": False,
                "error": {
                    "code": code if isinstance(code, str) else "ADAPTER_INTERNAL_ERROR",
                    "message": "Unexpected adapter failure",
                    "operation": "infer",
                    "component_id": self.COMPONENT_ID,
                    "retryable": False,
                    "details": {
                        "cause_type": type(unexpected_err).__name__,
                        "operation": "infer",
                    },
                },
            }

    def _classify_retryable(self, code: str, *, default: bool = False) -> bool:
        if code in self._RETRYABLE_CODES:
            return True
        if code in self._NON_RETRYABLE_CODES:
            return False
        return default


def create_adapter() -> VisionOrchestratorAdapter:
    """Entry Point Factory."""
    return VisionOrchestratorAdapter()
