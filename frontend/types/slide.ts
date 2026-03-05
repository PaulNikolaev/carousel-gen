/** Single slide from GET /api/v1/carousels/{id}/slides. */
export interface SlideResponse {
  id: string;
  carousel_id: string;
  order: number;
  title: string;
  body: string;
  footer: string;
  design_overrides: Record<string, unknown>;
}

/** Body for PATCH /api/v1/carousels/{id}/slides/{slide_id}. */
export interface SlideUpdate {
  title?: string;
  body?: string;
  footer?: string;
}
