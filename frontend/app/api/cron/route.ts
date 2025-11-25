import { NextResponse } from "next/server";

export async function GET(req: Request) {
  // --- Authorization (CRON_SECRET) ----
  const authHeader = req.headers.get("authorization");
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json(
      { error: "Unauthorized cron request" },
      { status: 401 }
    );
  }

  // --- Trigger backend pipeline run ----
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/pipeline/run`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${process.env.CRON_SECRET}`,
          "Content-Type": "application/json",
        },
      }
    );

    const data = await res.json();

    return NextResponse.json({
      ok: true,
      timestamp: new Date().toISOString(),
      backend_response: data,
    });
  } catch (error: any) {
    return NextResponse.json(
      {
        error: "Cron job failed",
        details: error?.message,
      },
      { status: 500 }
    );
  }
}

