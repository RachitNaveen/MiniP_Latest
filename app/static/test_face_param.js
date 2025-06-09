
console.log("Running face verification test");
try {
  // Create a simple test image (base64 encoded empty PNG) 
  let testImage = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";

  // Test request that mimics what face_modal.js now does
  fetch("/face/unlock_item", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      itemType: "message",
      itemId: "test123",
      face_image: testImage
    })
  })
  .then(response => response.json())
  .then(data => {
    console.log("Test response:", data);
    if (data.message === "Face image is required") {
      console.error("STILL FAILING: Backend is not finding the face_image parameter");
    } else {
      console.log("SUCCESS: Backend found the face_image parameter (though verification may still fail for other reasons)");
    }
  })
  .catch(error => {
    console.error("Test error:", error);
  });
} catch (e) {
  console.error("Test exception:", e);
}

