def user_info(request):
    """
    Context processor yang menyediakan informasi user untuk semua template
    """
    user_info = {
        'user_id': request.COOKIES.get('user_id', None),
        'user_email': request.COOKIES.get('user_email', None),
        'user_fullname': request.COOKIES.get('user_fullname', None),
        'user_role': request.COOKIES.get('user_role', None)
    }
    
    # Debugging 
    print("Context processor called:", user_info)
    
    return user_info