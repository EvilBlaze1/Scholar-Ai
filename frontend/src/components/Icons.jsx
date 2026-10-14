export function Icon({name,size=20,strokeWidth=1.8}){
  const p={width:size,height:size,viewBox:'0 0 24 24',fill:'none',stroke:'currentColor',strokeWidth,strokeLinecap:'round',strokeLinejoin:'round'}
  const paths={
    dashboard:<><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    search:<><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
    bookmark:<path d="M6 4.5A2.5 2.5 0 0 1 8.5 2h7A2.5 2.5 0 0 1 18 4.5V21l-6-3.7L6 21Z"/>,
    file:<><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h6"/></>,
    user:<><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></>,
    settings:<><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-1.7 1.7-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1.03 1.56V20h-2.4v-.2a1.7 1.7 0 0 0-1.03-1.56 1.7 1.7 0 0 0-1.88.34l-.06.06-1.7-1.7.06-.06A1.7 1.7 0 0 0 8.46 15a1.7 1.7 0 0 0-1.56-1.03H6v-2.4h.9A1.7 1.7 0 0 0 8.46 10a1.7 1.7 0 0 0-.34-1.88l-.06-.06 1.7-1.7.06.06a1.7 1.7 0 0 0 1.88.34 1.7 1.7 0 0 0 1.03-1.56V4h2.4v1.2a1.7 1.7 0 0 0 1.03 1.56 1.7 1.7 0 0 0 1.88-.34l.06-.06 1.7 1.7-.06.06A1.7 1.7 0 0 0 19.4 10c.2.6.75 1 1.38 1h.22v2.4h-.22c-.63 0-1.18.4-1.38 1.03Z"/></>,
    arrow:<path d="m9 18 6-6-6-6"/>,
    back:<><path d="m15 18-6-6 6-6"/><path d="M9 12h11"/></>,
    check:<path d="m5 12 4 4L19 6"/>,
    close:<><path d="M6 6l12 12M18 6 6 18"/></>,
    menu:<><path d="M4 6h16M4 12h16M4 18h16"/></>,
    logout:<><path d="M10 17l5-5-5-5M15 12H3M21 4v16"/></>,
    calendar:<><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></>,
    money:<><circle cx="12" cy="12" r="9"/><path d="M15 9.5c-.5-1-1.5-1.5-3-1.5-1.7 0-2.8.8-2.8 2 0 3 5.8 1 5.8 4 0 1.2-1.2 2-3 2-1.5 0-2.6-.5-3-1.5M12 6v12"/></>,
    spark:<path d="m12 3 1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5L12 3ZM19 16l.6 2.4L22 19l-2.4.6L19 22l-.6-2.4L16 19l2.4-.6L19 16Z"/>,
  }
  return <svg {...p}>{paths[name]}</svg>
}
