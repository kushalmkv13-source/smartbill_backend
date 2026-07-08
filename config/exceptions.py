import logging

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


logger = logging.getLogger(__name__)


# =====================================================
# GLOBAL DRF EXCEPTION HANDLER
# =====================================================

def custom_exception_handler(exc, context):

    # Let Django REST Framework handle known exceptions first
    response = exception_handler(exc, context)


    # =================================================
    # KNOWN DRF ERRORS
    #
    # Examples:
    # 400 - Validation Error
    # 401 - Authentication Error
    # 403 - Permission Error
    # 404 - Not Found
    # 405 - Method Not Allowed
    # 429 - Throttling Error
    # =================================================

    if response is not None:

        message = get_error_message(
            response.data
        )

        response.data = {
            "success": False,
            "message": message,
            "errors": response.data,
        }

        return response


    # =================================================
    # UNEXPECTED SERVER ERROR
    # =================================================

    request = context.get("request")
    view = context.get("view")


    logger.exception(
        "Unhandled API exception | view=%s | path=%s",
        (
            view.__class__.__name__
            if view
            else "Unknown"
        ),
        (
            request.path
            if request
            else "Unknown"
        ),
        exc_info=(
            type(exc),
            exc,
            exc.__traceback__,
        ),
    )


    return Response(
        {
            "success": False,
            "message":
                "An internal server error occurred."
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


# =====================================================
# GET USER-FRIENDLY ERROR MESSAGE
# =====================================================

def get_error_message(data):

    # =================================================
    # DICTIONARY ERROR
    # =================================================

    if isinstance(data, dict):

        # Standard DRF error
        if "detail" in data:

            return str(
                data["detail"]
            )


        # Serializer validation errors
        for value in data.values():

            if isinstance(value, list):

                if value:

                    first_error = value[0]

                    if isinstance(
                        first_error,
                        dict
                    ):

                        return get_error_message(
                            first_error
                        )

                    return str(
                        first_error
                    )


            if isinstance(value, dict):

                return get_error_message(
                    value
                )


            if isinstance(value, str):

                return value


    # =================================================
    # LIST ERROR
    # =================================================

    if isinstance(data, list):

        if data:

            first_error = data[0]

            if isinstance(
                first_error,
                (dict, list)
            ):

                return get_error_message(
                    first_error
                )

            return str(
                first_error
            )


    # =================================================
    # FALLBACK MESSAGE
    # =================================================

    return "Request failed."