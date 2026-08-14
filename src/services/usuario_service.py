"""
Servicio de negocio para la gestión de usuarios.
---------------------------------------------------
Responsabilidades:
    - Validar que el correo y el nombre de usuario sean únicos antes de crear.
    - Validar que la contraseña tenga seguridad mínima.
    - Devolver datos en esquemas Pydantic (no exponer el ORM directamente).

Este servicio hereda de BaseService para reutilizar métodos CRUD genéricos
y sobreélos con reglas de negocio propias del dominio de usuarios.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from src.models.usuario_model import Usuario
from src.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate, UsuarioResponse, UsuarioConCantidadCitas
from src.repositories.usuario_repository import UsuarioRepository
from src.services.base_service import BaseService


class UsuarioService(BaseService[Usuario]):
    """Servicio de negocio para usuarios (hereda de BaseService)."""

    def __init__(self, db: Session):
        repo = UsuarioRepository(db)
        super().__init__(db=db, repository=repo)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # ---------------------------------------------------------------
    #  CREATE (override con validación de negocio)
    # ---------------------------------------------------------------
    def crear_usuario(self, datos: UsuarioCreate, id = None) -> UsuarioResponse:
        """
        Reglas de negocio:
        1. El nombre de usuario (`usuario`) debe ser único en la BD.
        2. El correo (`correo`) debe ser único en la BD.
        3. La contraseña debe tener al menos 8 caracteres.
        4. La contraseña debe tener seguridad mínima (mayúsculas, minúsculas, números)

        Si `id` viene definido, significa que un administrador o recepcionista
        está creando el usuario: la contraseña se asigna automáticamente al
        número de identificación (`id_usuario`) y no es requisito proporcionarla.
        """
        if self._repo.exists(datos.id_usuario):
            raise ValueError("El usuario ya existe")
        
        # Regla 1: nombre de usuario único
        if self._repo.exists_usuario(datos.usuario):
            raise ValueError("El nombre de usuario ya está en uso")

        # Regla 2: correo único
        if self._repo.exists_correo(datos.correo):
            raise ValueError("El correo electrónico ya está registrado")

        if id is not None:
            # El administrador/recepcionista crea el usuario:
            # la contraseña pasa a ser el número de identificación (id_usuario)
            datos_contrasena_hashed = datos.model_copy()
            datos_contrasena_hashed.contraseña = self.hash_contraseña(str(datos.id_usuario))

            usuario_orm = self._repo.create(datos_contrasena_hashed)
            return UsuarioResponse.model_validate(usuario_orm)

        # Regla 3: contraseña mínima
        if len(datos.contraseña) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")

        # Regla 4: Validación de seguridad de contraseña
        # if not self._validar_seguridad_contraseña(datos.contraseña):
        #     raise ValueError("La contraseña debe contener al menos una mayúscula, una minúscula y un número")

        # Hash de contraseña antes de crear
        datos_contrasena_hashed = datos.model_copy()
        datos_contrasena_hashed.contraseña = self.hash_contraseña(datos.contraseña)

        usuario_orm = self._repo.create(datos_contrasena_hashed)
        return UsuarioResponse.model_validate(usuario_orm)

    def _validar_seguridad_contraseña(self, contraseña: str) -> bool:
        """Valida que la contraseña tenga seguridad mínima"""
        if len(contraseña) < 8:
            return False
        
        tiene_mayuscula = any(c.isupper() for c in contraseña)
        tiene_minuscula = any(c.islower() for c in contraseña)
        tiene_numero = any(c.isdigit() for c in contraseña)
        
        return tiene_mayuscula and tiene_minuscula and tiene_numero

    def hash_contraseña(self, contraseña: str) -> str:
        """Hashea la contraseña usando bcrypt"""
        return self.pwd_context.hash(contraseña)

    # ---------------------------------------------------------------
    #  READ
    # ---------------------------------------------------------------

    def listar_usuarios(self, skip: int = 0, limit: int = 100) -> List[UsuarioResponse]:
        usuarios = self._repo.get_all(skip, limit)
        return [UsuarioResponse.model_validate(usuario) for usuario in usuarios]

    def obtener_usuario_por_id(self, id_usuario: int) -> Optional[UsuarioResponse]:
        """Obtiene un usuario por su ID, si existe."""
        usuario = self._repo.get_by_id(id_usuario)
        if not usuario:
            return None
        return UsuarioResponse.model_validate(usuario)

    def obtener_por_usuario(self, nombre_usuario: str) -> Optional[UsuarioResponse]:
        """Busca un usuario por su nombre de usuario."""
        usuario = self._repo.get_by_usuario(nombre_usuario)
        if not usuario:
            return None
        return UsuarioResponse.model_validate(usuario)

    def buscar_usuarios(self, termino: str) -> List[UsuarioResponse]:
        """Busca usuarios que coincidan con `termino` en nombre, apellido, usuario o correo."""
        return [UsuarioResponse.model_validate(u) for u in self._repo.search(termino)]

    def obtener_clientes(self) -> List[UsuarioResponse]:
        """Obtiene solo los usuarios que NO son empleados (solo clientes)."""
        return [UsuarioResponse.model_validate(u) for u in self._repo.get_clientes()]

    # ---------------------------------------------------------------
    #  UPDATE (override con validación de negocio)
    # ---------------------------------------------------------------
    def actualizar_usuario(
        self, id_usuario: int, datos: UsuarioUpdate
    ) -> Optional[UsuarioResponse]:
        """
        Actualiza un usuario, validando que el nombre de usuario y el correo
        sigan siendo únicos (solo si fueron modificados).
        """
        usuario_actual = self._repo.get_by_id(id_usuario)
        if not usuario_actual:
            return None

        # Validar que no se repitan nombre de usuario o correo
        if datos.usuario and datos.usuario != usuario_actual.usuario:
            if self._repo.exists_usuario(datos.usuario):
                raise ValueError("El nombre de usuario ya está en uso")

        if datos.correo and datos.correo != usuario_actual.correo:
            if self._repo.exists_correo(datos.correo):
                raise ValueError("El correo electrónico ya está registrado")

        # Si se está actualizando la contraseña, hashearla
        if datos.contraseña:
            datos_actualizados = datos.model_copy()
            datos_actualizados.contraseña = self.hash_contraseña(datos.contraseña)
            usuario_actualizado = self._repo.update(id_usuario, datos_actualizados)
        else:
            usuario_actualizado = self._repo.update(id_usuario, datos)

        if not usuario_actualizado:
            return None
        return UsuarioResponse.model_validate(usuario_actualizado)

    # ---------------------------------------------------------------
    #  DELETE
    # ---------------------------------------------------------------
    def eliminar_usuario(self, id_usuario: int) -> bool:
        """Elimina un usuario. Devuelve True si se eliminó."""
        return self._repo.delete(id_usuario)

    # ---------------------------------------------------------------
    #  MÉTODOS ADICIONALES
    # ---------------------------------------------------------------
    
    def verificar_credenciales(self, nombre_usuario: str, contraseña: str) -> Optional[UsuarioResponse]:
        """
        Verifica las credenciales de un usuario.
        Retorna el usuario si las credenciales son correctas, None en caso contrario.
        """
        usuario = self._repo.get_by_usuario(nombre_usuario)
        if not usuario:
            return None
            
        # Verificar contraseña
        if self.pwd_context.verify(contraseña, usuario.contraseña):
            return UsuarioResponse.model_validate(usuario)
        return None

    def cambiar_contraseña(self, id_usuario: int, contraseña_actual: str, nueva_contraseña: str) -> bool:
        """
        Cambia la contraseña de un usuario si la contraseña actual es correcta.
        """
        # Primero verificar que la contraseña actual es correcta
        usuario = self._repo.get_by_id(id_usuario)
        if not usuario:
            return False
            
        if not self.pwd_context.verify(contraseña_actual, usuario.contraseña):
            return False
            
        # Validar nueva contraseña
        if len(nueva_contraseña) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
            
        if not self._validar_seguridad_contraseña(nueva_contraseña):
            raise ValueError("La contraseña debe contener al menos una mayúscula, una minúscula y un número")
            
        # Actualizar contraseña
        datos_actualizados = UsuarioUpdate(
            id_usuario=id_usuario,
            contraseña=nueva_contraseña
        )
        datos_actualizados.contraseña = self.hash_contraseña(nueva_contraseña)
        return self._repo.update(id_usuario, datos_actualizados) is not None

    # ---------------------------------------------------------------
    #  MÉTODOS AUXILIARES
    # ---------------------------------------------------------------
    def exists_usuario(self, nombre_usuario: str) -> bool:
        """Comprueba si existe un usuario con el nombre dado."""
        return self._repo.exists_usuario(nombre_usuario)

    def exists_correo(self, correo: str) -> bool:
        """Comprueba si existe un usuario con el correo dado."""
        return self._repo.exists_correo(correo)
    
    def obtener_usuarios_panel_admin(self) -> List[UsuarioConCantidadCitas]:
        return [UsuarioConCantidadCitas.model_validate(u) for u in self._repo.get_usuarios_con_cantidad_citas()]
    
    
    def obtener_perfil_usuario(self,id):
        return self._repo.get_perfil_cliente(id)
