-- CreateTable
CREATE TABLE "InsightImportBatch" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "filename" TEXT NOT NULL,
    "source" TEXT NOT NULL DEFAULT 'meta_business_suite_csv',
    "importedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "importedBy" TEXT,
    "fileHash" TEXT NOT NULL,
    "rowCount" INTEGER NOT NULL DEFAULT 0,
    "matchedCount" INTEGER NOT NULL DEFAULT 0,
    "unmatchedCount" INTEGER NOT NULL DEFAULT 0,
    "skippedCount" INTEGER NOT NULL DEFAULT 0,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "notes" TEXT,
    "rawColumnsJson" TEXT,
    "columnMappingJson" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "ImportedPostInsight" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "batchId" INTEGER NOT NULL,
    "source" TEXT NOT NULL DEFAULT 'meta_business_suite_csv',
    "postId" TEXT,
    "permalinkUrl" TEXT,
    "externalContentId" TEXT,
    "createdTime" TEXT,
    "messageSnippet" TEXT,
    "reach" INTEGER,
    "impressions" INTEGER,
    "engagedUsers" INTEGER,
    "clicks" INTEGER,
    "reactions" INTEGER,
    "comments" INTEGER,
    "shares" INTEGER,
    "videoViews" INTEGER,
    "watchTime" REAL,
    "rawRowJson" TEXT,
    "matchStatus" TEXT NOT NULL DEFAULT 'unmatched',
    "matchedPostId" TEXT,
    "matchConfidence" REAL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "ImportedPostInsight_batchId_fkey" FOREIGN KEY ("batchId") REFERENCES "InsightImportBatch" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "InsightImportBatch_fileHash_key" ON "InsightImportBatch"("fileHash");

-- CreateIndex
CREATE INDEX "InsightImportBatch_importedAt_idx" ON "InsightImportBatch"("importedAt");

-- CreateIndex
CREATE INDEX "InsightImportBatch_status_idx" ON "InsightImportBatch"("status");

-- CreateIndex
CREATE INDEX "ImportedPostInsight_batchId_idx" ON "ImportedPostInsight"("batchId");

-- CreateIndex
CREATE INDEX "ImportedPostInsight_matchStatus_idx" ON "ImportedPostInsight"("matchStatus");

-- CreateIndex
CREATE INDEX "ImportedPostInsight_matchedPostId_idx" ON "ImportedPostInsight"("matchedPostId");
