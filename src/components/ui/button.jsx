import React from 'react'

export function Button({ children, className='', variant='default', ...props }){
  const base = 'rounded-2xl px-6 py-2 font-medium shadow-md transition active:scale-[.98]'
  const variants = {
    default: 'bg-neutral-200 text-neutral-900 hover:bg-white',
    secondary: 'bg-neutral-800 text-neutral-100 hover:bg-neutral-700 border border-neutral-600'
  }
  return (
    <button className={`${base} ${variants[variant] ?? variants.default} ${className}`} {...props}>
      {children}
    </button>
  )
}
