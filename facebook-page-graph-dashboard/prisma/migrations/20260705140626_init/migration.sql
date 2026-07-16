-- CreateTable
CREATE TABLE "PageSnapshot" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "date" TEXT NOT NULL,
    "pageId" TEXT NOT NULL,
    "pageName" TEXT,
    "followersCount" INTEGER NOT NULL DEFAULT 0,
    "fanCount" INTEGER NOT NULL DEFAULT 0,
    "followersDelta" INTEGER DEFAULT 0,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "Post" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "fbPostId" TEXT NOT NULL,
    "pageId" TEXT NOT NULL,
    "message" TEXT,
    "permalinkUrl" TEXT,
    "createdTime" TEXT,
    "postType" TEXT NOT NULL DEFAULT 'unknown',
    "topic" TEXT NOT NULL DEFAULT 'khac',
    "reactionsCount" INTEGER NOT NULL DEFAULT 0,
    "commentsCount" INTEGER NOT NULL DEFAULT 0,
    "sharesCount" INTEGER NOT NULL DEFAULT 0,
    "reach" INTEGER,
    "impressions" INTEGER,
    "engagedUsers" INTEGER,
    "clicks" INTEGER,
    "engagementRate" REAL,
    "score" REAL,
    "rawJson" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "VideoMetric" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "fbVideoId" TEXT NOT NULL,
    "fbPostId" TEXT,
    "pageId" TEXT NOT NULL,
    "title" TEXT,
    "createdTime" TEXT,
    "views" INTEGER NOT NULL DEFAULT 0,
    "uniqueViews" INTEGER NOT NULL DEFAULT 0,
    "avgWatchTime" REAL,
    "reach" INTEGER,
    "reactionsCount" INTEGER NOT NULL DEFAULT 0,
    "commentsCount" INTEGER NOT NULL DEFAULT 0,
    "sharesCount" INTEGER NOT NULL DEFAULT 0,
    "rawJson" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "Comment" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "fbCommentId" TEXT NOT NULL,
    "fbPostId" TEXT NOT NULL,
    "pageId" TEXT NOT NULL,
    "message" TEXT,
    "createdTime" TEXT,
    "likeCount" INTEGER NOT NULL DEFAULT 0,
    "commentCount" INTEGER NOT NULL DEFAULT 0,
    "keywordFlag" TEXT,
    "sentiment" TEXT,
    "riskLevel" TEXT NOT NULL DEFAULT 'low',
    "status" TEXT NOT NULL DEFAULT 'new',
    "suggestedAction" TEXT,
    "suggestedReply" TEXT,
    "rawJson" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "Comment_fbPostId_fkey" FOREIGN KEY ("fbPostId") REFERENCES "Post" ("fbPostId") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "WeeklyReport" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "weekStart" TEXT NOT NULL,
    "weekEnd" TEXT NOT NULL,
    "reachTotal" INTEGER NOT NULL DEFAULT 0,
    "engagementTotal" INTEGER NOT NULL DEFAULT 0,
    "followerDelta" INTEGER NOT NULL DEFAULT 0,
    "topPostId" TEXT,
    "topTopic" TEXT,
    "summary" TEXT,
    "recommendation" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateIndex
CREATE INDEX "PageSnapshot_pageId_date_idx" ON "PageSnapshot"("pageId", "date");

-- CreateIndex
CREATE UNIQUE INDEX "PageSnapshot_pageId_date_key" ON "PageSnapshot"("pageId", "date");

-- CreateIndex
CREATE UNIQUE INDEX "Post_fbPostId_key" ON "Post"("fbPostId");

-- CreateIndex
CREATE INDEX "Post_pageId_createdTime_idx" ON "Post"("pageId", "createdTime");

-- CreateIndex
CREATE INDEX "Post_topic_idx" ON "Post"("topic");

-- CreateIndex
CREATE UNIQUE INDEX "VideoMetric_fbVideoId_key" ON "VideoMetric"("fbVideoId");

-- CreateIndex
CREATE INDEX "VideoMetric_pageId_createdTime_idx" ON "VideoMetric"("pageId", "createdTime");

-- CreateIndex
CREATE UNIQUE INDEX "Comment_fbCommentId_key" ON "Comment"("fbCommentId");

-- CreateIndex
CREATE INDEX "Comment_fbPostId_idx" ON "Comment"("fbPostId");

-- CreateIndex
CREATE INDEX "Comment_status_idx" ON "Comment"("status");

-- CreateIndex
CREATE INDEX "Comment_riskLevel_idx" ON "Comment"("riskLevel");

-- CreateIndex
CREATE INDEX "WeeklyReport_weekStart_idx" ON "WeeklyReport"("weekStart");

-- CreateIndex
CREATE UNIQUE INDEX "WeeklyReport_weekStart_weekEnd_key" ON "WeeklyReport"("weekStart", "weekEnd");
