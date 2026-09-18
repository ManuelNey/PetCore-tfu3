import { Outlet } from 'react-router-dom'
import Header from '../components/layout/Header'

// Shell general de la app: header fijo + slot de contenido.
function AppLayout() {
  return (
    <>
      <Header />
      <main>
        <Outlet />
      </main>
    </>
  )
}

export default AppLayout
