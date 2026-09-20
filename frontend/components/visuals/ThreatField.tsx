'use client'

import { useEffect, useRef } from 'react'

interface Point3D { x: number; y: number; z: number }
interface ScreenPoint { x: number; y: number; depth: number }

const nodes: Point3D[] = [
  { x: -3.3, y: 1.1, z: 1.4 }, { x: -1.7, y: 2.2, z: -0.6 },
  { x: -0.2, y: 1.45, z: 0.3 }, { x: 1.25, y: 2.75, z: 1.1 },
  { x: 2.95, y: 1.3, z: -0.5 }, { x: 1.1, y: .5, z: 1.8 },
]
const links = [[0,1],[0,2],[1,3],[2,3],[2,4],[3,4],[3,5],[4,5]] as const

export function ThreatField() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const context = canvas?.getContext('2d')
    if (!canvas || !context) return

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let frame = 0
    let animation = 0
    let width = 0
    let height = 0
    let ratio = 1

    const resize = () => {
      const rect = canvas.getBoundingClientRect()
      ratio = Math.min(window.devicePixelRatio || 1, 2)
      width = rect.width
      height = rect.height
      canvas.width = Math.round(width * ratio)
      canvas.height = Math.round(height * ratio)
      context.setTransform(ratio, 0, 0, ratio, 0, 0)
    }

    const line = (x1: number, y1: number, x2: number, y2: number, color: string, lineWidth = 1) => {
      context.beginPath(); context.moveTo(x1,y1); context.lineTo(x2,y2)
      context.strokeStyle=color; context.lineWidth=lineWidth; context.stroke()
    }

    const polygon = (points: Array<[number,number]>, fill: string, stroke: string) => {
      context.beginPath(); context.moveTo(points[0][0],points[0][1])
      points.slice(1).forEach(([x,y]) => context.lineTo(x,y)); context.closePath()
      context.fillStyle=fill; context.fill(); context.strokeStyle=stroke; context.lineWidth=1; context.stroke()
    }

    const project = (point: Point3D, yaw: number): ScreenPoint => {
      const cosine=Math.cos(yaw); const sine=Math.sin(yaw)
      const rotatedX=point.x*cosine-point.z*sine
      const rotatedZ=point.x*sine+point.z*cosine
      const perspective=1+rotatedZ*.055
      const scale=Math.min(width,height)*.075*perspective
      return { x:width*.56+rotatedX*scale, y:height*.63-point.y*scale+rotatedZ*scale*.18, depth:rotatedZ }
    }

    const block = (x: number, y: number, w: number, h: number, depth: number) => {
      const dx=depth*.62; const dy=-depth*.42
      const edge='rgba(126,158,202,.27)'
      polygon([[x,y],[x+dx,y+dy],[x+w+dx,y+dy],[x+w,y]],'rgba(28,39,58,.48)',edge)
      polygon([[x+w,y],[x+w+dx,y+dy],[x+w+dx,y+h+dy],[x+w,y+h]],'rgba(8,13,23,.64)',edge)
      const face=context.createLinearGradient(x,y,x+w,y+h)
      face.addColorStop(0,'rgba(19,29,44,.48)'); face.addColorStop(1,'rgba(5,9,16,.74)')
      context.fillStyle=face; context.fillRect(x,y,w,h); context.strokeStyle=edge; context.strokeRect(x,y,w,h)
      line(x+8,y+10,x+w-8,y+10,'rgba(136,170,214,.14)')
      for(let offset=25;offset<h;offset+=26) line(x,y+offset,x+w,y+offset,'rgba(115,145,184,.11)')
    }

    const tank = (x: number, y: number, w: number, h: number, depth: number) => {
      const dx=depth*.48; const dy=-depth*.34
      context.save(); context.translate(dx,dy)
      const face=context.createLinearGradient(x,y,x+w,y)
      face.addColorStop(0,'rgba(5,10,17,.72)'); face.addColorStop(.52,'rgba(31,45,64,.52)'); face.addColorStop(1,'rgba(5,10,17,.78)')
      context.fillStyle=face; context.fillRect(x,y,w,h)
      context.strokeStyle='rgba(126,158,202,.28)'; context.strokeRect(x,y,w,h)
      context.beginPath(); context.ellipse(x+w/2,y,w/2,8,0,0,Math.PI*2); context.fillStyle='rgba(25,38,56,.62)'; context.fill(); context.stroke()
      context.beginPath(); context.ellipse(x+w/2,y+h,w/2,8,0,0,Math.PI*2); context.stroke()
      for(let offset=26;offset<h;offset+=28) line(x,y+offset,x+w,y+offset,'rgba(115,145,184,.11)')
      context.restore()
      line(x+w/2+dx,y+dy-20,x+w/2+dx,y+dy,'rgba(126,158,202,.24)')
    }

    const plant = (drift: number) => {
      context.save(); context.translate(width*.53+drift,height*.69)
      context.shadowColor='rgba(25,77,150,.13)'; context.shadowBlur=22
      block(-190,-104,76,104,18); tank(-105,-168,62,168,20); block(-30,-128,104,128,22)
      tank(89,-206,58,206,24); block(166,-94,82,94,17)
      context.shadowBlur=0
      line(-210,-72,272,-72,'rgba(126,158,202,.34)',2)
      line(-210,-61,272,-61,'rgba(79,142,247,.18)')
      line(-176,0,-176,24,'rgba(126,158,202,.24)'); line(220,0,220,24,'rgba(126,158,202,.24)')
      context.restore()
    }

    const grid = (drift: number) => {
      const horizon=height*.7
      const vanishingX=width*.55+drift
      for(let i=-12;i<=12;i+=1) line(vanishingX+i*7,horizon-92,vanishingX+i*68,height,'rgba(79,142,247,.075)')
      for(let i=0;i<10;i+=1) {
        const progress=i/9; const y=horizon-92+Math.pow(progress,2.05)*(height-horizon+92)
        line(0,y,width,y,`rgba(79,142,247,${.04+progress*.045})`)
      }
      const floorGlow=context.createRadialGradient(vanishingX,horizon,0,vanishingX,horizon,width*.48)
      floorGlow.addColorStop(0,'rgba(79,142,247,.075)'); floorGlow.addColorStop(1,'rgba(79,142,247,0)')
      context.fillStyle=floorGlow; context.fillRect(0,horizon-120,width,height-horizon+120)
    }

    const draw = () => {
      context.clearRect(0,0,width,height)
      const drift=reduceMotion?0:Math.sin(frame*.004)*7
      const yaw=reduceMotion?.16:.16+Math.sin(frame*.004)*.075
      grid(drift); plant(drift*.55)

      const rawPoints=nodes.map((node)=>project(node,yaw))
      const points=[...rawPoints].sort((a,b)=>a.depth-b.depth)
      links.forEach(([start,end])=>{
        const a=rawPoints[start]; const b=rawPoints[end]; const mid=(a.x+b.x)/2
        context.beginPath(); context.moveTo(a.x,a.y+5); context.bezierCurveTo(mid,a.y+24,mid,b.y+24,b.x,b.y+5)
        context.strokeStyle='rgba(2,7,16,.72)'; context.lineWidth=4; context.stroke()
        const signal=context.createLinearGradient(a.x,a.y,b.x,b.y)
        signal.addColorStop(0,'rgba(79,142,247,.35)'); signal.addColorStop(.5,'rgba(107,163,249,.88)'); signal.addColorStop(1,'rgba(79,142,247,.42)')
        context.beginPath(); context.moveTo(a.x,a.y); context.bezierCurveTo(mid,a.y-12,mid,b.y-12,b.x,b.y)
        context.strokeStyle=signal; context.lineWidth=1.4; context.stroke()
      })

      points.forEach((point)=>{
        const originalIndex=rawPoints.findIndex((candidate)=>candidate===point)
        const color=originalIndex===3?'#FF3B30':originalIndex===2||originalIndex===4?'#FFB800':'#4F8EF7'
        const pulse=reduceMotion?0:Math.sin(frame*.03+originalIndex)*1.2
        const floorY=Math.min(height*.76,point.y+68+point.depth*5)
        line(point.x,point.y+8,point.x,floorY,`${color}32`)
        context.beginPath(); context.ellipse(point.x,floorY,12,3.5,0,0,Math.PI*2); context.strokeStyle=`${color}42`; context.stroke()
        context.save(); context.shadowColor=color; context.shadowBlur=11
        context.beginPath(); context.ellipse(point.x,point.y,10+pulse,7+pulse*.65,0,0,Math.PI*2)
        context.fillStyle='rgba(6,10,18,.9)'; context.fill(); context.strokeStyle=color; context.lineWidth=1.6; context.stroke()
        context.beginPath(); context.arc(point.x,point.y,2.7,0,Math.PI*2); context.fillStyle=color; context.fill()
        context.restore()
      })

      context.fillStyle='rgba(79,142,247,.38)'
      for(let i=0;i<5;i+=1) context.fillRect(width*.79+i*8,height*.86-i*5,1,8+i*5)
      frame+=1
      if(!reduceMotion) animation=window.requestAnimationFrame(draw)
    }

    resize()
    const observer=new ResizeObserver(()=>{resize(); if(reduceMotion) draw()})
    observer.observe(canvas); draw()
    return()=>{observer.disconnect(); window.cancelAnimationFrame(animation)}
  },[])

  return (
    <div className="threat-field relative h-full min-h-[420px] overflow-hidden" aria-label="Illustrative precursor relationship field">
      <div className="threat-field-plane absolute inset-0"><canvas ref={canvasRef} className="absolute inset-0 h-full w-full" /></div>
      <div className="absolute left-5 top-5 border-l border-accent pl-3 md:left-7 md:top-7">
        <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent">Precursor field</p>
        <p className="mt-1 max-w-56 text-xs leading-5 text-text-secondary">Hazards, causes, regulations and historical cases</p>
      </div>
      <div className="absolute bottom-5 right-5 text-right font-mono text-[9px] uppercase tracking-[0.14em] text-text-muted md:bottom-7 md:right-7">Analysis topology preview</div>
    </div>
  )
}
