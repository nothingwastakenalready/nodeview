interface LogoProps { withName?: boolean; className?: string; light?: boolean; }

export function Logo({ withName = false, className = "", light = false }: LogoProps) {
  return (
    <span className={`raffael-logo ${className}`} aria-label="Raffael">
      <img className="raffael-logo-image" src={light ? "/assets/02-logo-varianten/logo-liquid-silver-weiss-transparent.png" : "/assets/02-logo-varianten/logo-liquid-silver-schwarz-transparent.png"} alt="" />
      {withName ? <span className="raffael-logo-name">raffael</span> : null}
    </span>
  );
}
