import base64
import json
import logging
import time

from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions
from rest_framework.request import Request
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

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

        JWT_ACCESS_TOKEN_ENABLED = flag_set('fflag__feature_develop__prompts__dia_1829_jwt_token_auth')
        if JWT_ACCESS_TOKEN_ENABLED and (auth_result is not None):
            user, _ = auth_result
            org = user.active_organization
            org_id = org.id if org else None

            # raise 401 if legacy API token auth disabled (i.e. this token is no longer valid)
            if org and (not org.jwt.legacy_api_tokens_enabled):
                raise AuthenticationFailed(
                    'Authentication token no longer valid: legacy token authentication has been disabled for this organization'
                )

            logger.info(
                'Legacy token authentication used',
                extra={'user_id': user.id, 'organization_id': org_id, 'endpoint': request.path},
            )
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


class SSOJWTAuthentication(authentication.BaseAuthentication):
    """
    自定义 JWT Token 认证类，用于 SSO 统一登录认证
    支持从 Header 或 URL 参数中获取 token
    自动创建本地用户（如果不存在）
    """

    def parser_token(self, access_token):
        """解析 JWT payload（不验证签名，仅解码）"""
        try:
            parts = access_token.split('.')
            if len(parts) != 3:
                raise ValueError("Token must have 3 parts")
            _, payload, _ = parts
            # 补齐 Base64 padding
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded.decode('utf-8'))
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            logger.error(f'Fail to parser token, error: {e}')
            raise exceptions.AuthenticationFailed('Invalid token format')

    def authenticate(self, request: Request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '').strip()

        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
        elif auth_header.startswith('Token '):
            token = auth_header.split(' ', 1)[1]
        elif auth_header:
            token = auth_header

        if not token:
            token = request.GET.get('token')

        if not token:
            return None  # 跳过认证

        try:
            payload = self.parser_token(token)
            # 测试时注释过期时间
            # exp = payload.get('exp')
            # if exp is not None:
            #     if not isinstance(exp, (int, float)):
            #         raise exceptions.AuthenticationFailed('Invalid expiration time in token')
            #     if time.time() > exp:
            #         raise exceptions.AuthenticationFailed('Token expired')
            # print('payload', payload)
            user_info = payload.get('userInfo')
            if not user_info:
                raise exceptions.AuthenticationFailed('Token missing userInfo')

            user_code = user_info.get('userCode')
            user_name = user_info.get('userName', '')

            if not user_code:
                raise exceptions.AuthenticationFailed('userCode is required in token')

            User = get_user_model()   # 内部调用
            user, created = User.objects.get_or_create(
                username=user_code,
                defaults={
                    'email': f'{user_code}@yto.net.cn',
                    'first_name': user_name[:30] if user_name else user_code,
                    'is_active': True
                }
            )

            if not user.is_active:
                raise exceptions.AuthenticationFailed('User account disabled')

            return (user, token)

        except exceptions.AuthenticationFailed:
            raise
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')

    def authenticate_header(self, request):
        return 'Bearer realm="api"'
