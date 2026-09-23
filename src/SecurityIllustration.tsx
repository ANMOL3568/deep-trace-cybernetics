export default function SecurityIllustration() {
  return <svg className="security-laptop" viewBox="0 0 640 500" role="img" aria-label="Secure laptop with a digital lock and connected security devices">
    <defs>
      <linearGradient id="screen" x2="1" y2="1"><stop stopColor="#126286"/><stop offset="1" stopColor="#062540"/></linearGradient>
      <linearGradient id="metal" x2=".8" y2="1"><stop stopColor="#e6faff"/><stop offset="1" stopColor="#5caacb"/></linearGradient>
      <linearGradient id="lock" x2="1" y2="1"><stop stopColor="#8effff"/><stop offset="1" stopColor="#04a4d3"/></linearGradient>
      <radialGradient id="glow"><stop stopColor="#05bfd4" stopOpacity=".2"/><stop offset="1" stopColor="#05bfd4" stopOpacity="0"/></radialGradient>
    </defs>
    <ellipse cx="338" cy="304" rx="275" ry="170" fill="url(#glow)"/>
    <g fill="none" stroke="#175371" strokeWidth="1">
      <path d="m60 266 291-169 236 137-284 166Z M54 324l242 140 293-170 M148 187l303 175 M207 151l303 175 M92 287l298-172 M133 331l298-172"/>
      <path d="M310 103V74l169-38 M481 386l81 47 M89 220l-47-28 M207 412v39"/>
    </g>
    <g fill="none" strokeWidth="1.5">
      <ellipse cx="329" cy="281" rx="231" ry="116" stroke="#ab4484" transform="rotate(-12 329 281)"/>
      <ellipse cx="329" cy="281" rx="218" ry="102" stroke="#126f97" transform="rotate(-12 329 281)"/>
      <ellipse cx="329" cy="281" rx="206" ry="91" stroke="#964580" transform="rotate(-12 329 281)"/>
    </g>
    <path d="m201 289 178-101 158 89-178 107Z" fill="#021627" opacity=".7"/>
    <path d="m258 263 5-155q0-13 12-6l211 121q8 5 8 16l-4 153Z" fill="#0f425f" stroke="#81e5f4" strokeWidth="2" transform="translate(-18 -40)"/>
    <path d="m263 111 214 123-4 137-214-122Z" fill="url(#screen)" stroke="#2982a7" transform="translate(-18 -40)"/>
    <g strokeLinecap="round" strokeWidth="3" opacity=".9">
      <path d="m376 185 48 28m-48-15 59 34m-59-20 28 16m-28-3 51 29m-51-16 38 22" stroke="#27c7e1"/>
      <path d="m414 234 26 15m-17 4 13 8m-60-19 24 14" stroke="#cf62b9"/>
    </g>
    <path d="m240 223 231 133-126 74q-9 5-18 0L103 301Z" fill="url(#metal)" stroke="#a2e4f7" strokeWidth="2"/>
    <path d="m103 301 224 129q9 5 18 0l126-74v10l-126 73q-9 5-18 0L103 311Z" fill="#367d9e"/>
    <path d="m242 241 184 107-77 44-183-105Z" fill="#174a68" stroke="#62a6bd"/>
    <g stroke="#82c5dd" strokeWidth="2" opacity=".85">
      {[0,1,2,3,4,5].map(i=><path key={i} d={`m${181+i*12} ${285-i*7} 169 98`}/>)}
      {[0,1,2,3,4,5,6,7,8,9,10].map(i=><path key={i} d={`m${191+i*16} ${298+i*9} 57-33`}/>)}
    </g>
    <path d="m194 329 58 33-29 17-58-34Z" fill="#afddeb" stroke="#5798b2"/>
    <g transform="translate(257 140)">
      <path d="M21 86V34C21-8 82 2 82 47v40" fill="none" stroke="#176a92" strokeWidth="17"/>
      <path d="M17 84V32C17-10 78 0 78 45v40" fill="none" stroke="#91f1ff" strokeWidth="9"/>
      <path d="M29 88V34c0-25 36-18 36 10v38" fill="none" stroke="#18b4da" strokeWidth="3"/>
      <path d="m0 71 87 32v82L0 151Z" fill="url(#lock)" stroke="#b1f9ff" strokeWidth="2"/>
      <path d="m87 103 12-7v81l-12 8" fill="#1387ae"/>
      <ellipse cx="44" cy="119" rx="7" ry="10" fill="#075177" transform="rotate(-15 44 119)"/>
      <path d="m42 123-3 20 12 4-4-22" fill="#075177"/>
    </g>
    <g transform="translate(472 353) rotate(-29)"><rect width="73" height="116" rx="8" fill="#387f9a" stroke="#abdeec" strokeWidth="2"/><rect x="5" y="9" width="63" height="91" rx="3" fill="#092e49"/><path d="m36 29 20 10v23q0 16-20 25-20-9-20-25V39Z" fill="#11b8ce33" stroke="#32cadb"/><path d="m27 57 7 8 15-19" fill="none" stroke="#8cffff" strokeWidth="3"/><circle cx="37" cy="108" r="3" fill="#b3eaf4"/></g>
    <g transform="translate(122 163)"><path d="m0 0 32-13 30 27v38q-2 28-30 38Q2 63 0 39Z" fill="#0f5c77" stroke="#76e9f5" strokeWidth="2"/><path d="m17 32 14 18 19-30" fill="none" stroke="#68edf3" strokeWidth="4"/></g>
    <g fill="#08d1e7" stroke="#48e0ed"><path d="m102 123 22-13 22 13-22 13Z M57 238l19-11 19 11-19 11Z M523 153l22-13 22 13-22 13Z M559 315l19-11 19 11-19 11Z M568 411l19-11 19 11-19 11Z"/></g>
    <g fill="#c7f5ff"><path d="m170 110 7-4 7 4-7 4Z M475 105l7-4 7 4-7 4Z M104 365l7-4 7 4-7 4Z M406 443l7-4 7 4-7 4Z"/></g>
  </svg>;
}
