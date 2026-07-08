from .models import AuditLog


# =====================================================
# GET CLIENT IP ADDRESS
# =====================================================

def get_client_ip(request):

    if not request:
        return None

    forwarded_for = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if forwarded_for:

        # First address is the original client IP
        return forwarded_for.split(",")[0].strip()

    return request.META.get(
        "REMOTE_ADDR"
    )


# =====================================================
# CREATE AUDIT LOG
# =====================================================

def create_audit_log(
    request,
    action,
    description="",
    user=None
):

    try:

        # Use authenticated request user when
        # a user was not explicitly supplied.
        if user is None:

            request_user = getattr(
                request,
                "user",
                None
            )

            if (
                request_user
                and request_user.is_authenticated
            ):
                user = request_user


        ip_address = get_client_ip(request)


        user_agent = ""

        if request:

            user_agent = request.META.get(
                "HTTP_USER_AGENT",
                ""
            )


        AuditLog.objects.create(

            user=user,

            action=action,

            description=description,

            ip_address=ip_address,

            user_agent=user_agent[:1000],
        )


    except Exception:

        # Audit logging failure should not break
        # the main API operation.
        return None