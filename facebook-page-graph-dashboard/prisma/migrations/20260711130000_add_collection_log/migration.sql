-- AlterTable
ALTER TABLE "BenchmarkPage" ADD COLUMN "collectionErrors" TEXT;
ALTER TABLE "BenchmarkPage" ADD COLUMN "collectionStatus" TEXT;
ALTER TABLE "BenchmarkPage" ADD COLUMN "lastCollectedAt" DATETIME;

-- CreateTable
CREATE TABLE "CollectionLog" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "benchmarkPageId" INTEGER NOT NULL,
    "status" TEXT NOT NULL,
    "source" TEXT NOT NULL DEFAULT 'fb_session_collector',
    "postsCollected" INTEGER NOT NULL DEFAULT 0,
    "postsWithError" INTEGER NOT NULL DEFAULT 0,
    "followerCount" INTEGER,
    "rawSnapshot" TEXT,
    "errors" TEXT,
    "collectedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "CollectionLog_benchmarkPageId_fkey" FOREIGN KEY ("benchmarkPageId") REFERENCES "BenchmarkPage" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE INDEX "CollectionLog_benchmarkPageId_collectedAt_idx" ON "CollectionLog"("benchmarkPageId", "collectedAt");

┌─────────────────────────────────────────────────────────┐
│  Update available 5.22.0 -> 7.8.0                       │
│                                                         │
│  This is a major update - please follow the guide at    │
│  https://pris.ly/d/major-version-upgrade                │
│                                                         │
│  Run the following to update                            │
│    npm i --save-dev prisma@latest                       │
│    npm i @prisma/client@latest                          │
└─────────────────────────────────────────────────────────┘
