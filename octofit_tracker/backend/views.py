import logging
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

def sample_view(request):
    try:
        # Simulate some logic that could raise an exception
        result = 1 / 0  # Example of an error
        return JsonResponse({'result': result})
    except ZeroDivisionError as e:
        logger.error(f"Error in sample_view: {e}")
        return JsonResponse({'error': 'An error occurred'}, status=500)
    except Exception as e:
        logger.exception(f"Unexpected error in sample_view: {e}")
        return JsonResponse({'error': 'Unexpected error occurred'}, status=500)

class InputData(BaseModel):
    name: str
    age: int

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sample_api(request):
    try:
        # Validate input data
        data = InputData(**request.data)
        logger.info(f"Received valid data: {data}")
        return Response({'message': 'Data processed successfully'}, status=status.HTTP_200_OK)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return Response({'error': 'Invalid input data', 'details': e.errors()}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
