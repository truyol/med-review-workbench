from dataclasses import dataclass
from http import HTTPStatus


@dataclass
class ApiError(Exception):
    code: str
    message: str
    next_action: str
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR


def project_not_found() -> ApiError:
    return ApiError(
        code="PROJECT_NOT_FOUND",
        message="Project was not found.",
        next_action="Refresh the project list or create a project first.",
        status_code=HTTPStatus.NOT_FOUND,
    )


def case_not_found() -> ApiError:
    return ApiError(
        code="CASE_NOT_FOUND",
        message="Case was not found.",
        next_action="Refresh the case list or create a case first.",
        status_code=HTTPStatus.NOT_FOUND,
    )


def asset_not_found() -> ApiError:
    return ApiError(
        code="ASSET_NOT_FOUND",
        message="Asset was not found.",
        next_action="Refresh the review board and try again.",
        status_code=HTTPStatus.NOT_FOUND,
    )


def duplicate_case_code() -> ApiError:
    return ApiError(
        code="CASE_CODE_CONFLICT",
        message="Case code already exists in this project.",
        next_action="Use a unique case code within the same project.",
        status_code=HTTPStatus.CONFLICT,
    )


def unsupported_asset_type() -> ApiError:
    return ApiError(
        code="UNSUPPORTED_ASSET_TYPE",
        message="Only DICOM, STL, PNG, and JPEG files are supported.",
        next_action="Upload a supported, de-identified review asset.",
        status_code=HTTPStatus.BAD_REQUEST,
    )


def model_parse_failed() -> ApiError:
    return ApiError(
        code="MODEL_PARSE_FAILED",
        message="STL model content could not be parsed.",
        next_action="Export a valid binary or ASCII STL file and upload again.",
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
    )


def image_parse_failed() -> ApiError:
    return ApiError(
        code="IMAGE_PARSE_FAILED",
        message="Image content could not be decoded.",
        next_action="Upload a valid PNG or JPEG image and try again.",
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
    )


def persistence_failed() -> ApiError:
    return ApiError(
        code="PERSISTENCE_FAILED",
        message="The change could not be saved.",
        next_action="Retry the operation; if it persists, provide the request_id to support.",
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
    )


def preview_not_available() -> ApiError:
    return ApiError(
        code="PREVIEW_NOT_AVAILABLE",
        message="Preview is not available for this asset.",
        next_action="Use the asset metadata or upload a previewable image/DICOM file.",
        status_code=HTTPStatus.CONFLICT,
    )


def model_not_available() -> ApiError:
    return ApiError(
        code="MODEL_NOT_AVAILABLE",
        message="3D model content is not available for this asset.",
        next_action="Select an STL asset or upload a supported model file.",
        status_code=HTTPStatus.CONFLICT,
    )


def asset_file_missing() -> ApiError:
    return ApiError(
        code="ASSET_FILE_MISSING",
        message="Stored asset file is missing.",
        next_action="Re-upload the asset or check storage configuration.",
        status_code=HTTPStatus.NOT_FOUND,
    )


def upload_too_large() -> ApiError:
    return ApiError(
        code="UPLOAD_TOO_LARGE",
        message="Uploaded file exceeds the configured size limit.",
        next_action="Reduce the file size or raise the configured limit for this environment.",
        status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
    )


def asset_delete_restricted() -> ApiError:
    return ApiError(
        code="DELETE_RESTRICTED",
        message="Reviewed assets cannot be hard deleted.",
        next_action="Keep the review history and mark the asset out of scope instead.",
        status_code=HTTPStatus.CONFLICT,
    )


def annotation_not_found() -> ApiError:
    return ApiError(
        code="ANNOTATION_NOT_FOUND",
        message="Annotation was not found.",
        next_action="Refresh the asset annotations and try again.",
        status_code=HTTPStatus.NOT_FOUND,
    )
