import {Icon} from './Icons'

const items=[['dashboard','Overview','dashboard'],['search','Scholarships','scholarships'],['bookmark','Saved','saved'],['file','Applications','applications'],['user','Profile','profile']]

export default function Layout({page,setPage,user,onLogout,children}){
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark">S</div><div><strong>Scholar AI</strong><span>Scholarship finder</span></div></div>
      <nav className="nav-list">{items.map(([icon,label,key])=><button key={key} className={`nav-item ${page===key?'active':''}`} onClick={()=>setPage(key)}><Icon name={icon}/><span>{label}</span></button>)}</nav>
      <div className="sidebar-bottom"><button className={`nav-item ${page==='settings'?'active':''}`} onClick={()=>setPage('settings')}><Icon name="settings"/><span>Settings</span></button><div className="user-mini"><div className="avatar">{(user?.email||'S')[0].toUpperCase()}</div><div><b>{user?.email?.split('@')[0]||'Student'}</b><span>Student account</span></div><button title="Log out" onClick={onLogout}><Icon name="logout" size={18}/></button></div></div>
    </aside>
    <main className="main-area"><header className="topbar"><button className="mobile-menu" onClick={()=>document.body.classList.toggle('menu-open')}><Icon name="menu"/></button><div className="top-search" onClick={()=>setPage('scholarships')}><Icon name="search" size={18}/><span>Search scholarships...</span><kbd>⌘ K</kbd></div><div className="top-actions"><div className="top-avatar">{(user?.email||'S')[0].toUpperCase()}</div></div></header><div className="content">{children}</div></main>
  </div>
}
