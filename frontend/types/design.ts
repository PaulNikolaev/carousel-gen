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
};
