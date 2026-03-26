from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

from account.tokens import generate_email_confirm_token, generate_temporary_password, verify_email_confirm_token
from account.email_send import send_email
from account.api_endpoints.auth.serealizers import RegisterINputSErializer, ConfirmTokenSerializer


User = get_user_model()


class RegisterUserAPIView(APIView):
    @swagger_auto_schema(request_body=RegisterINputSErializer)
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email va parol kiritilishi kerak."},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing = User.objects.filter(email=email, is_active=True).first()

        if existing:
            if not existing.is_confirmed:
                token = generate_email_confirm_token(existing)
                new_pass = generate_temporary_password()
                existing.set_password(new_pass)
                existing.save()

                send_email(
                    subject="Tasdiqlash havolasi orqali parolingizga start bering!",
                    intro_text="Tasdiqlash uchun quyidagi havolani bosing!",
                    email=email,
                    token=token,
                    template='email/reset_password_email.html',
                    password=new_pass,
                )

                return Response(
                    {
                        "detail": (
                            "Foydalanuvchi allaqachon mavjud, lekin tasdiqlanmagan! "
                            "Tasdiqlash havolasi va vaqtinchalik parol yuborildi."
                        )
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(
                {"detail": "Foydalanuvchi allaqachon mavjud va tasdiqlangan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(email=email, password=password, is_confirmed=False)
        token = generate_email_confirm_token(user)

        send_email(
            subject="Tasdiqlash havolasi!",
            intro_text="E-mailni tasdiqlash uchun quyidagi havolani bosing!",
            email=email,
            token=token,
            template='email/reset_password_email.html',
        )

        return Response(
            {"detail": "Foydalanuvchi muvaffaqiyatli ruyxatdan utdi. Tasdiqlash uchun havola yuborildi."},
            status=status.HTTP_201_CREATED,
        )


class RegisterConfirmAPIView(APIView):
    @swagger_auto_schema(request_body=ConfirmTokenSerializer)
    def post(self, request):
        token = request.data.get("token")

        if not token:
            return Response(
                {"detail": "Token talab qilinadi va taqdim etilmadi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = verify_email_confirm_token(token)

        if not user_id:
            return Response(
                {"detail": "Token yaroqsiz yoki muddati utgan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Foydalanuvchi topilmadi."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_confirmed:
            return Response(
                {"detail": "Foydalanuvchi allaqachon tasdiqlangan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_confirmed = True
        user.save()

        return Response(
            {"detail": "Foydalanuvchi muvaffaqiyatli tasdiqlandi."},
            status=status.HTTP_200_OK,
        )
