/**
 * Marchio "CruScout".
 *
 * Doppia lettura voluta: "cru" e' il termine enologico per la vigna di
 * pregio, ma per un lettore italiano CruScout suona come "cruscotto" — il
 * quadro strumenti dove il produttore legge profilo chimico, qualita'
 * stimata, prezzo e abbinamenti in un colpo d'occhio. E' la lettura che
 * governa il payoff, ed e' anche quella che il sistema mantiene davvero:
 * il dataset non contiene terroir ne' origine geografica.
 *
 * La testa del sommelier sta accanto alla parola, non dentro: sostituire
 * una lettera con l'icona sembrava elegante sulla carta ma alla lettura
 * spezzava il nome.
 */
import { SommelierMark } from "./RobotSommelierIcon";

interface BrandLockupProps {
  /** "header" per la navbar, "hero" per usi piu' grandi. */
  variant?: "header" | "hero";
}

export function BrandLockup({ variant = "header" }: BrandLockupProps) {
  const isHero = variant === "hero";

  return (
    <span className={`brand-lockup ${isHero ? "hero" : "header"}`}>
      <SommelierMark size={isHero ? 74 : 42} />
      <span className="brand-lockup-word">
        Cru<span className="brand-lockup-accent">Scout</span>
      </span>
    </span>
  );
}
