import { useState, useEffect } from "react";
import { useLoaderData, useNavigation, useRevalidator } from "@remix-run/react";
import {
  Page,
  Layout,
  Card,
  Badge,
  Button,
  ProgressBar,
  EmptyState,
  SkeletonPage,
  SkeletonBodyText,
  Frame,
  BlockStack,
  InlineStack,
  Text,
  Box,
} from "@shopify/polaris";
import { TitleBar, useAppBridge } from "@shopify/app-bridge-react";
import { authenticate } from "../shopify.server";
import { createApiClient } from "../services/api";
import { JobsService } from "../services/jobs";
import { useAppBridgeNavigation } from "../utils/appBridge";

/**
 * Job Detail Loader
 * Fetches a single job with full details and logs
 * Requirements: 11.7
 */
export const loader = async ({ request, params }) => {
  try {
    const { sessionToken } = await authenticate.admin(request);
    const api = await createApiClient(request, sessionToken);
    const jobsService = new JobsService(api);

    const jobId = parseInt(params.id);
    const job = await jobsService.get(jobId);

    return {
      job,
    };
  } catch (error) {
    console.error("Job detail loader error:", error);
    throw error;
  }
};

/**
 * Job Detail Component
 * Displays detailed job information with logs and progress
 * Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
 */
export default function JobDetail() {
  const data = useLoaderData();
  const navigation = useNavigation();
  const revalidator = useRevalidator();
  const shopify = useAppBridge();
  const navigate = useAppBridgeNavigation();

  const isLoading = navigation.state === "loading";
  const job = data?.job;

  // Auto-refresh for active jobs every 5 seconds
  // Requirements: 11.8
  useEffect(() => {
    if (!job || (job.status !== "running" && job.status !== "pending")) return;

    const interval = setInterval(() => {
      revalidator.revalidate();
    }, 5000);

    return () => clearInterval(interval);
  }, [job, revalidator]);

  // Get status badge tone
  const getStatusTone = (status) => {
    switch (status) {
      case "completed":
        return "success";
      case "failed":
        return "critical";
      case "running":
      case "pending":
        return "warning";
      default:
        return "default";
    }
  };

  // Calculate job duration
  const calculateDuration = (startedAt, completedAt) => {
    if (!startedAt) return "-";
    
    const start = new Date(startedAt);
    const end = completedAt ? new Date(completedAt) : new Date();
    const durationMs = end - start;
    const durationSeconds = Math.floor(durationMs / 1000);
    
    if (durationSeconds < 60) {
      return `${durationSeconds}s`;
    } else if (durationSeconds < 3600) {
      const minutes = Math.floor(durationSeconds / 60);
      const seconds = durationSeconds % 60;
      return `${minutes}m ${seconds}s`;
    } else {
      const hours = Math.floor(durationSeconds / 3600);
      const minutes = Math.floor((durationSeconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  };

  // Show loading skeleton
  if (isLoading || !job) {
    return (
      <SkeletonPage>
        <Layout>
          <Layout.Section>
            <Card>
              <BlockStack gap="300">
                <SkeletonBodyText lines={3} />
              </BlockStack>
            </Card>
          </Layout.Section>
          <Layout.Section>
            <Card>
              <BlockStack gap="300">
                <SkeletonBodyText lines={10} />
              </BlockStack>
            </Card>
          </Layout.Section>
        </Layout>
      </SkeletonPage>
    );
  }

  return (
    <Frame>
      <Page
        backAction={{
          onAction: () => {
            window.location.href = "/app/jobs";
          },
        }}
      >
        <TitleBar title={`Job #${job.id}`} />
        <Layout>
          {/* Job Info Card */}
          <Layout.Section>
            <Card>
              <BlockStack gap="400">
                <InlineStack align="space-between">
                  <BlockStack gap="100">
                    <Text variant="headingMd" as="h2">
                      {job.job_type}
                    </Text>
                    <Badge tone={getStatusTone(job.status)}>
                      {job.status}
                    </Badge>
                  </BlockStack>
                </InlineStack>

                <BlockStack gap="200">
                  <Box>
                    <Text variant="bodyMd" as="p">
                      <strong>Progress:</strong> {job.progress}%
                    </Text>
                    <ProgressBar progress={job.progress} />
                  </Box>
                </BlockStack>

                <BlockStack gap="200">
                  <Text variant="bodyMd" as="p">
                    <strong>Started:</strong> {job.started_at ? new Date(job.started_at).toLocaleString() : "-"}
                  </Text>
                  <Text variant="bodyMd" as="p">
                    <strong>Completed:</strong> {job.completed_at ? new Date(job.completed_at).toLocaleString() : "In progress"}
                  </Text>
                  <Text variant="bodyMd" as="p">
                    <strong>Duration:</strong> {calculateDuration(job.started_at, job.completed_at)}
                  </Text>
                </BlockStack>

                {job.error_message && (
                  <BlockStack gap="200">
                    <Text variant="bodyMd" as="p" tone="critical">
                      <strong>Error:</strong> {job.error_message}
                    </Text>
                  </BlockStack>
                )}
              </BlockStack>
            </Card>
          </Layout.Section>

          {/* Logs Card */}
          {job.logs && job.logs.length > 0 && (
            <Layout.Section>
              <Card>
                <BlockStack gap="300">
                  <Text variant="headingMd" as="h3">
                    Logs
                  </Text>
                  <Box
                    padding="300"
                    background="bg-surface-secondary"
                    borderRadius="200"
                    overflowX="auto"
                  >
                    <BlockStack gap="200">
                      {job.logs.map((log, index) => (
                        <Box key={index}>
                          <Text variant="bodySm" as="p" tone="subdued">
                            <strong>[{new Date(log.timestamp).toLocaleTimeString()}]</strong> {log.message}
                          </Text>
                        </Box>
                      ))}
                    </BlockStack>
                  </Box>
                </BlockStack>
              </Card>
            </Layout.Section>
          )}

          {/* Actions Card */}
          <Layout.Section>
            <Card>
              <BlockStack gap="300">
                <Button
                  variant="secondary"
                  onClick={() => {
                    window.location.href = "/app/jobs";
                  }}
                >
                  Back to Jobs
                </Button>
              </BlockStack>
            </Card>
          </Layout.Section>
        </Layout>
      </Page>
    </Frame>
  );
}
