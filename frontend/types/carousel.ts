/** Carousel status from API. */
export type CarouselStatus = "draft" | "generating" | "ready" | "failed";

/** Source type for create. */
export type SourceType = "text" | "video" | "links";

/** Format options for create (slides_count 6–10, language, style_hint). */
export interface CarouselFormat {
  slides_count?: number;
  language?: string;
  style_hint?: string;
}

/** Body for POST /api/v1/carousels. */
export interface CreateCarouselPayload {
  title?: string;
  source_type: SourceType;
  source_payload: Record<string, unknown>;
  format?: CarouselFormat;
}

/** Single carousel item from GET /api/v1/carousels. */
export interface CarouselResponse {
  id: string;
  title: string;
  source_type: string;
  source_payload: Record<string, unknown>;
  format: Record<string, unknown>;
  status: CarouselStatus;
  language: string;
  slides_count: number;
  created_at: string;
  updated_at: string;
  preview_url: string;
}

/** Paginated list from GET /api/v1/carousels. */
export interface CarouselListResponse {
  items: CarouselResponse[];
  total: number;
}
