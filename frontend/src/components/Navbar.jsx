import { NavLink } from 'react-router-dom'
import { Boxes } from 'lucide-react'

export default function Navbar() {
  return (
    <header className="topbar">
      <NavLink to="/" className="brand">
        <span className="brand-mark">
          <Boxes size={18} strokeWidth={2.5} />
        </span>
        <div>
          <div>SMARTORDER AI</div>
          <div className="brand-sub">OrdEasy · Eaton Prototype</div>
        </div>
      </NavLink>

      <nav className="nav-links">
        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          Dashboard
        </NavLink>
        <NavLink to="/upload" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          Upload Order
        </NavLink>
        <NavLink to="/chat" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          Chat Assistant
        </NavLink>
      </nav>
    </header>
  )
}
