from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import User
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer,CvSerializer
from django.core.files.storage import default_storage
from ai.extract_freelancer_info import parse_cv
from jobs.models import FreelancerProfile as freelancerProfile

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing users
    
    retrieve:
    Return a user instance.

    list:
    Return all users, ordered by most recently joined.

    create:
    Create a new user.
    Accessible without authentication for registration purposes.

    update:
    Update all fields of a user instance.
    Requires authentication and ownership of the account.

    partial_update:
    Update one or more fields of a user instance.
    Requires authentication and ownership of the account.

    delete:
    Delete a user instance.
    Requires authentication and ownership of the account.
    """
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    """
    API endpoint for user login
    """
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

class UploadCVView(APIView):
    """
    API endpoint to upload and process a user's CV
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CvSerializer

    @swagger_auto_schema(
        operation_description="Upload and process a CV file for a user. Authentication required.",
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                in_=openapi.IN_PATH,
                description="ID of the user",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'cv',
                in_=openapi.IN_FORM,
                description="CV file to upload (PDF or DOCX)",
                type=openapi.TYPE_FILE,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="CV uploaded and processed successfully",
                examples={
                    "application/json": {
                        "detail": "CV uploaded and processed successfully.",
                        "profile": {
                            "skills": ["Python", "Django", "REST APIs"],
                            "experience_years": 5,
                            "hourly_rate": 50,
                            "job_type": "full_time",
                            "category": "web_development"
                        }
                    }
                }
            ),
            400: openapi.Response(description="No CV file provided"),
            401: openapi.Response(description="Authentication credentials were not provided"),
            404: openapi.Response(description="User not found")
        },
        operation_summary="Upload CV"
    )
    def post(self, request, user_id):
        print("hhhhh------------------------------------")
        print("Request data:", request.data['file'])
        try:
            user = User.objects.get(id=user_id)
            data=request.data
            
            if data.get('file'):
                print("hhhhh---------------------------------")
                print("Validated data:", data)
                cv_file = data['file']
                file_path = f'cvs/{user_id}_{cv_file.name}'
                default_storage.save(file_path, cv_file)
                abs_path = default_storage.path(file_path)
                profile = freelancerProfile.objects.get_or_create(user=user)[0]
                profile.cv = abs_path
                extracted_info = parse_cv(abs_path)
                print("hhh------------------------------------")
                return Response({
                    'is_success': True,
                    'detail': 'CV uploaded and processed successfully.',
                    'profile': extracted_info
                }, status=status.HTTP_200_OK)
            return Response({'is_success': False, 'detail': 'No CV file provided.'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'is_success': False, 'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

