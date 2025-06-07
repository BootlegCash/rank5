@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    API endpoint to get the authenticated user's profile data.
    This version includes debugging to check for a missing profile.
    """
    user = request.user
    try:
        # This is the line that is likely failing
        profile = user.profile

        # If it succeeds, it returns the normal profile data
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": profile.display_name,
            "xp": profile.xp,
            "rank": profile.rank,
            "total_alcohol": profile.total_alcohol
        })
    except Profile.DoesNotExist:
        # If user.profile fails, instead of crashing with a 500 error,
        # we will now return a 404 error with a specific message.
        return Response(
            {"error": "Profile not found for this user. This confirms the profile was not created on registration."},
            status=status.HTTP_404_NOT_FOUND
        )
