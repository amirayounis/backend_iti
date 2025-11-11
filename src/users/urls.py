from rest_framework.routers import DefaultRouter
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserViewSet, RegisterView, LoginView, UploadCVView

router = DefaultRouter()
router.register(r'', UserViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('upload-cv/<int:user_id>/', UploadCVView.as_view(), name='upload_cv'),
    path('', include(router.urls)),
]