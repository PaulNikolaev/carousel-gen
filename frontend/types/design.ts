/** Design snapshot for slide preview (from GET design or default). */
export interface DesignSnapshot {
  template: "classic" | "bold" | "minimal"; // "minimal" was "soft" in earlier spec
  background_type: "color" | "image";
  background_value: string;
  /** Applied as rgba overlay on image backgrounds (implemented in step 7.x). */
  overlay: number;
  padding: number;
  alignment_h: "left" | "center" | "right";
  alignment_v: "top" | "center" | "bottom";
  header_enabled: boolean;
  header_text: string;
  footer_enabled: boolean;
  footer_text: string;
  font_size: number;
  font_family: string;
  font_weight: "normal" | "bold";
  font_style: "normal" | "italic";
}

/** Partial payload for PATCH /api/v1/carousels/{id}/design. */
export interface DesignUpdate {
  template?: DesignSnapshot["template"];
  background?: {
    type?: DesignSnapshot["background_type"];
    value?: string;
    overlay?: number;
  };
  layout?: {
    padding?: number;
    alignment_h?: DesignSnapshot["alignment_h"];
    alignment_v?: DesignSnapshot["alignment_v"];
  };
  header?: { enabled?: boolean; text?: string };
  footer?: { enabled?: boolean; text?: string };
  typography?: {
    font_size?: number;
    font_family?: string;
    font_weight?: DesignSnapshot["font_weight"];
    font_style?: DesignSnapshot["font_style"];
  };
}

/** Response from GET /api/v1/carousels/{id}/design. */
export interface DesignResponse {
  design: DesignSnapshot;
}

/** Default design when backend has no GET design endpoint (step 7.2). */
export const DEFAULT_DESIGN: DesignSnapshot = {
  template: "classic",
  background_type: "color",
  background_value: "#FFFFFF",
  overlay: 0,
  padding: 24,
  alignment_h: "center",
  alignment_v: "center",
  header_enabled: true,
  header_text: "",
  footer_enabled: true,
  footer_text: "",
  font_size: 16,
  font_family: "system-ui",
  font_weight: "normal",
  font_style: "normal",
};

/** Response from PATCH .../design (carousel + design snapshot). */
export interface CarouselWithDesignResponse {
  id: string;
  title: string;
  status: string;
  design: DesignSnapshot;
  [key: string]: unknown;
}
