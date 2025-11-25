import { NextResponse } from "next/server";

export async function GET(req: Request) {
  const timestamp = new Date().toISOString();
  console.log(`[Cron] Job started at ${timestamp}`);

  // --- Authorization (CRON_SECRET) ----
  const authHeader = req.headers.get("authorization");
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    console.log(`[Cron] Unauthorized request - invalid or missing CRON_SECRET`);
    return NextResponse.json(
      { error: "Unauthorized cron request" },
      { status: 401 }
    );
  }

  console.log(`[Cron] Authorization successful`);

  // --- Trigger backend pipeline run ----
  try {
    const backendUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}/pipeline/run`;
    console.log(`[Cron] Calling backend: ${backendUrl}`);

    const res = await fetch(backendUrl, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.CRON_SECRET}`,
        "Content-Type": "application/json",
      },
    });

    const data = await res.json();

    if (!res.ok) {
      console.error(`[Cron] Backend returned error: ${res.status}`, data);
    } else {
      console.log(`[Cron] Backend pipeline completed successfully`);
    }

    return NextResponse.json({
      ok: true,
      timestamp: timestamp,
      backend_response: data,
    });
  } catch (error: any) {
    console.error(`[Cron] Error during pipeline execution:`, error?.message);
    return NextResponse.json(
      {
        error: "Cron job failed",
        details: error?.message,
      },
      { status: 500 }
    );
  }
}

