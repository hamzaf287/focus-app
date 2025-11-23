const videoFeed = document.getElementById("videoFeed");
const cameraStatus = document.getElementById("cameraStatus");
let statsInterval = null;

// Function to update live stats
async function updateLiveStats() {
  try {
    const response = await fetch("/live_stats");
    const stats = await response.json();

    if (stats.is_running) {
      document.getElementById("focusPercent").innerText = stats.focus_percentage + "%";
      document.getElementById("totalFrames").innerText = stats.total_frames;
    }
  } catch (error) {
    console.error("Error fetching live stats:", error);
  }
}

document.getElementById("startBtn").addEventListener("click", async () => {
  // Get selected course
  const selectedCourse = document.getElementById("courseSelect").value;

  const response = await fetch("/start", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ course: selectedCourse })
  });
  const data = await response.json();
  console.log(data.status, "Course:", data.course);

  videoFeed.src = "/video_feed";
  videoFeed.classList.add("active"); // Show video feed
  cameraStatus.style.display = "none"; // Hide status message

  // Reset stats
  document.getElementById("focusPercent").innerText = "0%";
  document.getElementById("totalFrames").innerText = "0";

  // Start polling live stats every 2 seconds
  statsInterval = setInterval(updateLiveStats, 2000);

  document.getElementById("startBtn").disabled = true;
  document.getElementById("stopBtn").disabled = false;
});

document.getElementById("stopBtn").addEventListener("click", async () => {
  // Stop polling live stats
  if (statsInterval) {
    clearInterval(statsInterval);
    statsInterval = null;
  }

  const response = await fetch("/stop", { method: "POST" });
  const data = await response.json();
  console.log(data.status);

  videoFeed.src = "";
  videoFeed.classList.remove("active"); // Hide video feed
  cameraStatus.style.display = "block"; // Show status message
  cameraStatus.innerHTML = '<i class="fas fa-camera"></i> Camera inactive - Start a session to begin';
  document.getElementById("reportContent").innerText = data.report;

  // Update final stats
  if (data.stats) {
    document.getElementById("focusPercent").innerText = data.stats.focus_percentage + "%";
    document.getElementById("totalFrames").innerText = data.stats.total_frames;
  }

  // Show download PDF button
  document.getElementById("downloadPdfBtn").style.display = "flex";

  document.getElementById("startBtn").disabled = false;
  document.getElementById("stopBtn").disabled = true;
});

// Download PDF button handler
document.getElementById("downloadPdfBtn").addEventListener("click", () => {
  window.location.href = "/download_report_pdf";
});
