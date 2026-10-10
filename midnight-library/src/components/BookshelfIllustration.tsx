const C = {
  ink: "#201A24",
  paper: "#F2E7D5",
  brass: "#C58A4A",
  sage: "#789080",
  burgundy: "#A95F61",
  plum: "#4A3550",
  plumDark: "#2B2230",
  aubergine: "#3A2B3F",
};

interface Book {
  w: number;
  h: number;
  c: string;
  mark?: boolean;
}

const ROW_A: Book[] = [
  { w: 24, h: 96, c: C.plumDark, mark: true },
  { w: 30, h: 118, c: C.burgundy },
  { w: 22, h: 84, c: C.sage },
  { w: 30, h: 104, c: C.aubergine, mark: true },
  { w: 26, h: 136, c: C.brass },
  { w: 26, h: 94, c: C.plumDark },
  { w: 24, h: 112, c: C.plum, mark: true },
  { w: 34, h: 110, c: C.sage },
  { w: 28, h: 120, c: C.burgundy, mark: true },
  { w: 30, h: 90, c: C.plum },
];

const ROW_B: Book[] = [
  { w: 28, h: 80, c: C.plum },
  { w: 26, h: 98, c: C.burgundy },
  { w: 32, h: 90, c: C.sage, mark: true },
  { w: 24, h: 76, c: C.plumDark },
  { w: 30, h: 104, c: C.brass },
  { w: 24, h: 88, c: C.aubergine },
  { w: 28, h: 96, c: C.plum, mark: true },
  { w: 26, h: 84, c: C.sage },
  { w: 30, h: 100, c: C.burgundy },
  { w: 28, h: 78, c: C.plum },
];

function Row({
  books,
  baseline,
  startX,
}: {
  books: Book[];
  baseline: number;
  startX: number;
}) {
  let x = startX;
  return (
    <>
      {books.map((b, i) => {
        const bx = x;
        x += b.w + 4;
        const top = baseline - b.h;
        return (
          <g key={i}>
            <rect x={bx} y={top} width={b.w} height={b.h} rx={2} fill={b.c} />
            {b.mark && (
              <>
                <line
                  x1={bx + 5}
                  x2={bx + b.w - 5}
                  y1={top + 14}
                  y2={top + 14}
                  stroke={C.brass}
                  strokeOpacity={0.7}
                />
                <line
                  x1={bx + 5}
                  x2={bx + b.w - 5}
                  y1={top + 19}
                  y2={top + 19}
                  stroke={C.brass}
                  strokeOpacity={0.7}
                />
              </>
            )}
          </g>
        );
      })}
    </>
  );
}

function Tag({
  x,
  y,
  label,
  w,
}: {
  x: number;
  y: number;
  label: string;
  w: number;
}) {
  return (
    <g transform={`translate(${x} ${y}) rotate(-2)`}>
      <rect width={w} height={18} rx={2} fill={C.ink} />
      <text
        x={w / 2}
        y={12.5}
        textAnchor="middle"
        fontSize={8.5}
        fontWeight={700}
        letterSpacing={1.6}
        fill={C.paper}
        style={{ fontFamily: "var(--font-dm-sans), sans-serif" }}
      >
        {label}
      </text>
    </g>
  );
}

export default function BookshelfIllustration({
  variant = "hero",
  className = "",
}: {
  variant?: "hero" | "row";
  className?: string;
}) {
  if (variant === "row") {
    return (
      <svg
        viewBox="0 0 420 190"
        className={className}
        aria-hidden="true"
        focusable="false"
      >
        <Row books={ROW_A} baseline={170} startX={55} />
        <line
          x1={45}
          x2={375}
          y1={171}
          y2={171}
          stroke={C.brass}
          strokeWidth={3}
          strokeOpacity={0.55}
        />
      </svg>
    );
  }

  return (
    <svg
      viewBox="0 0 440 470"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <radialGradient id="lampGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={C.brass} stopOpacity={0.28} />
          <stop offset="100%" stopColor={C.brass} stopOpacity={0} />
        </radialGradient>
        <filter id="cardShadow" x="-20%" y="-20%" width="140%" height="160%">
          <feGaussianBlur stdDeviation={8} />
        </filter>
      </defs>

      {/* Lamp + glow */}
      <ellipse
        className="animate-lamp"
        cx={220}
        cy={200}
        rx={210}
        ry={240}
        fill="url(#lampGlow)"
      />
      <line x1={220} x2={220} y1={0} y2={32} stroke={C.brass} strokeOpacity={0.5} />
      <path
        d="M168 70 Q168 32 220 32 Q272 32 272 70"
        fill={C.aubergine}
        stroke={C.brass}
        strokeOpacity={0.7}
      />
      <rect x={158} y={68} width={124} height={6} rx={3} fill={C.brass} />

      {/* Cabinet */}
      <rect
        x={40}
        y={130}
        width={360}
        height={270}
        fill={C.plumDark}
        fillOpacity={0.55}
        stroke={C.brass}
        strokeOpacity={0.3}
      />

      <Row books={ROW_A} baseline={275} startX={62} />
      <line x1={48} x2={392} y1={277} y2={277} stroke={C.brass} strokeWidth={2} strokeOpacity={0.55} />

      <Row books={ROW_B} baseline={385} startX={62} />
      <line x1={48} x2={392} y1={387} y2={387} stroke={C.brass} strokeWidth={2} strokeOpacity={0.55} />

      {/* Genre tags */}
      <Tag x={198} y={232} label="FANTASY" w={64} />
      <Tag x={92} y={304} label="MYSTERY" w={62} />
      <Tag x={272} y={316} label="ROMANCE" w={66} />

      {/* Card */}
      <g transform="translate(58 392) rotate(-3)">
        <rect x={4} y={10} width={290} height={64} rx={4} fill="#000" opacity={0.45} filter="url(#cardShadow)" />
        <rect width={290} height={64} rx={4} fill={C.paper} />
        <rect width={9} height={64} rx={3} fill={C.burgundy} />
        <text
          x={30}
          y={28}
          fontSize={17}
          fontStyle="italic"
          fill={C.ink}
          style={{ fontFamily: "var(--font-cormorant), serif" }}
        >
          One story,
        </text>
        <text
          x={30}
          y={48}
          fontSize={17}
          fontStyle="italic"
          fill={C.ink}
          style={{ fontFamily: "var(--font-cormorant), serif" }}
        >
          many shelves.
        </text>
        <line x1={30} x2={80} y1={56} y2={56} stroke={C.brass} />
      </g>
    </svg>
  );
}