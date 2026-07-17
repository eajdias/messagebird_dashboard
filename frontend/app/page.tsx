export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold">MBird Dashboard</h1>
      <p className="mt-4 text-muted-foreground">
        Omnichannel Reporting — Bird API
      </p>
      <div className="mt-8 flex gap-4">
        <a
          href="/dashboard"
          className="rounded-md bg-primary px-4 py-2 text-primary-foreground hover:opacity-90"
        >
          Dashboard
        </a>
        <a
          href="/login"
          className="rounded-md border px-4 py-2 hover:bg-accent"
        >
          Login
        </a>
      </div>
    </main>
  );
}
