import type * as React from "react";

type DragStyle = React.CSSProperties & {
  WebkitAppRegion?: "drag" | "no-drag";
};

export const dragRegion: DragStyle = { WebkitAppRegion: "drag" };
export const noDragRegion: DragStyle = { WebkitAppRegion: "no-drag" };
