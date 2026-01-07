import base64
import json
import logging
import jwt

from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions
from rest_framework.request import Request
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import TokenAuthentication


logger = logging.getLogger(__name__)


class TokenAuthenticationPhaseout(TokenAuthentication):
    """TokenAuthentication with features to help phase out legacy token auth

    Logs usage and triggers a 401 if legacy token auth is not enabled for the organization."""

    def authenticate(self, request):
        """Authenticate the request and log if successful."""
        from core.current_request import CurrentContext
        from core.feature_flags import flag_set

        auth_result = super().authenticate(request)

        # Update CurrentContext with authenticated user
        if auth_result is not None:
            user, _ = auth_result
            CurrentContext.set_user(user)

        return auth_result


class JWTAuthScheme(OpenApiAuthenticationExtension):
    target_class = 'jwt_auth.auth.TokenAuthenticationPhaseout'
    name = 'Token'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'The token (or API key) must be passed as a request header. '
            'You can find your user token on the User Account page in Label Studio. Example: '
            '<br><pre><code class="language-bash">'
            'curl https://label-studio-host/api/projects -H "Authorization: Token [your-token]"'
            '</code></pre>',
            'x-fern-header': {
                'name': 'api_key',
                'env': 'LABEL_STUDIO_API_KEY',
                'prefix': 'Token ',
            },
        }


User = get_user_model()


class CustomJWTAuthentication(authentication.BaseAuthentication):
    """
    自定义 JWT Token 认证类  用于SSO统一登录认证
    支持从 Header 或 URL 参数中获取 token
    """

    def parser_token(self, access_token):
        _, payload, _ = access_token.split('.')
        payload += '==='  #
        res = base64.urlsafe_b64decode(payload)
        return json.loads(res.decode())

    def authenticate(self, request: Request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        elif auth_header.startswith('Token '):
            token = auth_header.split(' ')[1]
        else:
            token = auth_header

        if not token:
            token = request.GET.get('token')

        # 如果没有 token，跳过认证（交给其他认证类或权限控制）
        if not token:
            return None  # DRF 会继续尝试其他认证类，或最终视为匿名用户

        try:
            payload = self.parser_token(token)
            user_info = payload.get('userInfo')
            if not user_info:
                raise exceptions.AuthenticationFailed('Invalid token payload')
            user_code = user_info.get('userCode')
            username = user_info.get('userName')
            user = User.objects.get(username=user_code)
            if not user.is_active:
                raise exceptions.AuthenticationFailed('User inactive')

            # 返回 (user, token) — DRF 要求的格式
            return (user, token)

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            # TODO 创建新用户
            raise exceptions.AuthenticationFailed('User not found')

    def authenticate_header(self, request):
        """
        返回 WWW-Authenticate 头，用于 401 响应
        """
        return 'Bearer realm="api"'

