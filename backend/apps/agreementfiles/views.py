import boto3
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
import os
from PilotWebsite.settings import AGREEMENT_BUCKET_NAME

s3 = boto3.client(
  's3'
)
bucket_name = AGREEMENT_BUCKET_NAME

@api_view(['POST'])
def upload_file(request):
  file = request.FILES['file']
  filename = request.POST.get('filename')
  fileType = request.POST.get('fileType')
  category = request.POST.get('category')

  #CHECK for file validity
  if not file:
    return Response({'error': 'No file uploaded'}, status=400)

  if not fileType == 'PDF':
    return Response({'error': 'Invalid file format. Must be a PDF file'}, status=400)

  if file.size > 10 * 1024 * 1024:  # 10MB limit
    return Response({'error': 'File size exceeds the limit'}, status=400)

  #TODO check for malicous content

  try:
    s3.upload_fileobj(file, bucket_name, filename, ExtraArgs={'Metadata': {'category': category}})
  except Exception as e:
    return Response({'error': str(e)}, status=500)

  return Response({'message': 'File uploaded successfully'}, status=200)

@api_view(['GET'])
def list_files(request):
  try:
    response = s3.list_objects_v2(Bucket=bucket_name)
    files = []
    for obj in response.get('Contents', []):
      filename = obj['Key']
      file_type = 'pdf' if filename.endswith('.pdf') else 'Unknown'
      metadata_response = s3.head_object(Bucket=bucket_name, Key=filename)
      category = metadata_response.get('Metadata', {}).get('category', 'Unknown')
      files.append({
        'filename': filename,
        'dateAdded': obj['LastModified'].strftime('%Y-%m-%d'),
        'category': category
      })

    return Response({'files': files})
  except Exception as e:
    return Response({'error': 'Failed to retrieve files'}, status=500)

  return Response({'message': 'File retrieved successfully'}, status=200)

@api_view(['DELETE'])
def delete_file(request, filename):
  try:
    s3.delete_object(Bucket=bucket_name, Key=filename)
    return Response({'message': 'File deleted successfully'}, status=204)
  except Exception as e:
    return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def download_file(request, filename):
  try:
    response = s3.get_object(Bucket=bucket_name, Key=filename)
    file_content = response['Body'].read()
    http_response = HttpResponse(file_content, content_type='application/pdf')
    http_response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return http_response
  except Exception as e:
    return Response({'error': str(e)}, status=500)