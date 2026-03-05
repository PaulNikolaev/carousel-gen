/** Carousel status from API. */
export type CarouselStatus = "draft" | "generating" | "ready" | "failed";

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
  created_at: string | null;
  updated_at: string | null;
  preview_url: string | null;
}

/** Paginated list from GET /api/v1/carousels. */
export interface CarouselListResponse {
  items: CarouselResponse[];
  total: number;
}
