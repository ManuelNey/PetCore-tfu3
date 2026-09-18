from pydantic import BaseModel

class VeterinarioResponse(BaseModel):
    id_usuario: int
    nombre: str
    apellido: str
    matricula_profesional: str