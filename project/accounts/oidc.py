from django.contrib.auth import get_user_model


def get_user(id_token):
    User = get_user_model()
    # user is admin if Administrateurs defined in user groups, realm roles or client roles
    # is_admin = "Administrateurs" in set(
    #     id_token.get("groups", [])
    #     + id_token.get("realm_access", {}).get("roles", [])
    #     + id_token.get("resource_access", {})
    #     .get("back1-xxxxx", {})
    #     .get("roles", [])
    # )

    # print(id_token)

    # is_staff = is_admin or "Gestion des Utilisateurs" in set(
    #    id_token.get("groups", []) + id_token.get("realm_access", {}).get("roles", [])
    # )
    # keep "sub -> internal keycloak id" for user identifier (case where user change its email)
    user, created = User.objects.update_or_create(
        email=id_token.get("email"),
        defaults={
            "properties": {
                "openid_sub": id_token.get("sub"),
            }
        },
    )

    return user
