/** Status of an export job. */
export type ExportStatus = "pending" | "running" | "done" | "failed";

/** Response of POST /api/v1/exports (202). */
export interface StartExportResponse {
  export_id: string;
}

/** Response of GET /api/v1/exports/{id}. */
export interface ExportResponse {
  id: string;
  carousel_id: string;
  status: ExportStatus;
  download_url?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}
