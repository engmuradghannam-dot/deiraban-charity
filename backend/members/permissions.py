from rest_framework.permissions import BasePermission


class IsApprovedMember(BasePermission):
    """يسمح فقط للعضو المعتمد (بعد موافقة الإدارة)."""
    message = 'يجب أن تكون عضواً معتمداً في الجمعية.'

    def has_permission(self, request, view):
        member = getattr(request.user, 'member_profile', None)
        return bool(
            request.user
            and request.user.is_authenticated
            and member
            and member.status == 'approved'
        )
