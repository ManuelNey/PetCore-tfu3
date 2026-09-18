import { createContext, useContext, useEffect, useState } from 'react'
import { login as loginRequest, obtenerUsuarioActual } from '../api/auth'

const AuthContext = createContext(null)

const TOKEN_KEY = 'petcore_token'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [usuario, setUsuario] = useState(null)
  // Mientras se resuelve el /me inicial (al recargar la página) no sabemos
  // todavía si hay sesión, así que las rutas protegidas esperan este flag
  // en vez de decidir con un usuario todavía vacío.
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    if (!token) {
      setCargando(false)
      return
    }

    obtenerUsuarioActual(token)
      .then(setUsuario)
      .catch(() => {
        // Token vencido o inválido: se descarta la sesión guardada.
        localStorage.removeItem(TOKEN_KEY)
        setToken(null)
        setUsuario(null)
      })
      .finally(() => setCargando(false))
  }, [token])

  async function login(correo, contrasena) {
    const respuesta = await loginRequest(correo, contrasena)

    localStorage.setItem(TOKEN_KEY, respuesta.access_token)
    setToken(respuesta.access_token)
    setUsuario(respuesta.usuario)

    return respuesta.usuario
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUsuario(null)
  }

  const value = {
    usuario,
    token,
    cargando,
    estaAutenticado: Boolean(usuario),
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (context === null) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider')
  }

  return context
}
