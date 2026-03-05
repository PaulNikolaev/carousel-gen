/** Status of a generation job. */
export type GenerationStatus = "queued" | "running" | "done" | "failed";

/** Single item from GET /api/v1/carousels/{id}/generations. */
export interface GenerationListItem {
  id: string;
  created_at: string;
  status: GenerationStatus;
  tokens_used: number | null;
}

/** Response of GET /api/v1/carousels/{id}/generations. */
export interface CarouselGenerationsResponse {
  items: GenerationListItem[];
}

/** Response of POST /api/v1/generations (202). */
export interface StartGenerationResponse {
  generation_id: string;
  tokens_estimate: number;
}

/** Single slide in GET generation result (when status=done). */
export interface GenerationSlideItem {
  order: number;
  title: string;
  body: string;
  footer: string;
}

/** Response of GET /api/v1/generations/{id}. */
export interface GenerationResponse {
  id: string;
  carousel_id: string;
  status: GenerationStatus;
  tokens_estimate: number | null;
  tokens_used: number | null;
  result: GenerationSlideItem[] | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}
