from rest_framework.response import Response
from rest_framework import status


def success_response(data, message=None):
    """
    Return a standardized success response.
    """
    response_data = {
        'success': True,
        'data': data
    }
    if message:
        response_data['message'] = message
    return Response(response_data, status=status.HTTP_200_OK)


def error_response(error_code, error_message, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Return a standardized error response.
    """
    return Response({
        'success': False,
        'error': {
            'code': error_code,
            'message': error_message
        }
    }, status=status_code)


def paginate_response(queryset, paginator, page_number, serializer_class):
    """
    Paginate a queryset and return standardized response.
    """
    page = paginator.paginate_queryset(queryset, page_number)
    serializer = serializer_class(page, many=True)
    
    return {
        'items': serializer.data,
        'pagination': {
            'current_page': paginator.page.number,
            'total_pages': paginator.page.paginator.num_pages,
            'total_items': paginator.page.paginator.count,
            'items_per_page': paginator.page_size
        }
    }
