from rest_framework.permissions import BasePermission


class IsApprovedMember(BasePermission):
    """يسمح بالتصويت فقط لحساب معتمد مرتبط بعضو فاعل في سجل الجمعية."""

    message = "يجب أن يكون حسابك معتمداً ومرتبطاً بعضو فاعل في سجل الجمعية للتصويت."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        member = getattr(request.user, "member_profile", None)
        return bool(member and member.is_eligible_to_vote)
