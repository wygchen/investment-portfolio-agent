"use client"

import dynamic from "next/dynamic"

const DiscoveryFlow = dynamic(() => import("@/components/discovery-flow").then(m => m.DiscoveryFlow), {
  ssr: false,
  loading: () => null,
})

export default function AssessmentPage() {
  return <DiscoveryFlow />
}