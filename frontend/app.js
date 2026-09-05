let currentLesson = null;
let currentSceneIndex = 0;
let currentQuizIndex = 0;
let studentPerformance = []; 

const synth = window.speechSynthesis;
let teacherVoice = null;

const avatarVideo = document.getElementById("avatar-video");
avatarVideo.src = "presenter.mp4"; 
avatarVideo.loop = true;
avatarVideo.pause();

speechSynthesis.onvoiceschanged = () => {
  const voices = synth.getVoices();
  teacherVoice = voices.find(v => 
    v.name.includes("Female") || v.name.includes("Zira") || v.name.includes("Google UK English Female")
  ) || voices[0];
};

document.getElementById("setup-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("btn-generate");
  btn.innerText = "Building Cinematic Lesson...";
  btn.disabled = true;

  const formData = new FormData();
  const fileInput = document.getElementById("doc-upload");
  if (fileInput.files[0]) formData.append("file", fileInput.files[0]);
  formData.append("topic", document.getElementById("topic-input").value);
  formData.append("level", document.getElementById("level-select").value);
  formData.append("time_limit", document.getElementById("time-input").value);
  formData.append("language", document.getElementById("lang-select").value);

  try {
    const res = await fetch("http://localhost:8000/api/start-lesson", {
      method: "POST",
      body: formData
    });
    
    const result = await res.json();
    currentLesson = result.data;
    studentPerformance = []; 
    currentSceneIndex = 0;
    currentQuizIndex = 0;
    
    document.getElementById("config-panel").style.display = "none";
    document.getElementById("classroom").style.display = "grid";
    
    // Hide quiz panel initially
    document.getElementById("checkpoint-container").style.display = "none";
    
    // Start continuous playback
    playScene();
    
  } catch (err) {
    alert("System Error: " + err.message);
  } finally {
    btn.innerText = "Generate AI Lesson";
    btn.disabled = false;
  }
});

function playScene() {
  if (currentSceneIndex >= currentLesson.lesson_sections.length) {
    // Lesson is over, start the quiz phase
    startQuizPhase();
    return;
  }

  const scene = currentLesson.lesson_sections[currentSceneIndex];
  
  // Update HUD
  document.getElementById("holo-step-tag").innerText = `SCENE 0${currentSceneIndex + 1}`;
  document.getElementById("speech-bubble").innerText = scene.script;
  
  // Smoothly fade in the new AI generated image
  const imgElement = document.getElementById("slideshow-img");
  imgElement.style.opacity = 0;
  setTimeout(() => {
    imgElement.src = scene.image_url + "?t=" + new Date().getTime();
    imgElement.style.opacity = 1;
  }, 500); // half second fade
  
  // Speak the script for this scene
  synth.cancel(); 
  const utterance = new SpeechSynthesisUtterance(scene.script);
  utterance.voice = teacherVoice;
  utterance.rate = 0.85; 
  utterance.pitch = 1.1; 
  
  utterance.onstart = () => avatarVideo.play();
  
  // When the paragraph finishes, automatically trigger the next scene
  utterance.onend = () => {
    avatarVideo.pause();
    currentSceneIndex++;
    playScene(); 
  };
  
  synth.speak(utterance);
}

function startQuizPhase() {
  document.getElementById("holo-step-tag").innerText = `FINAL ASSESSMENT`;
  document.getElementById("speech-bubble").innerText = "Let's test what you've learned. Answer the following questions.";
  
  const imgElement = document.getElementById("slideshow-img");
  imgElement.src = "models/dice.webm"; // Or leave the last image
  
  document.getElementById("checkpoint-container").style.display = "block";
  renderQuizQuestion();
}

function renderQuizQuestion() {
  if (currentQuizIndex >= currentLesson.final_quiz.length) {
    generateFinalReport();
    return;
  }

  const q = currentLesson.final_quiz[currentQuizIndex];
  const lang = document.getElementById("lang-select").value;
  
  document.getElementById("question-text").innerText = q.question;
  const optBox = document.getElementById("options-box");
  optBox.innerHTML = "";
  document.getElementById("misconception-box").style.display = "none";
  document.getElementById("btn-next-module").style.display = "none";
  
  q.options.forEach((opt) => {
    const b = document.createElement("button");
    b.className = "option-btn";
    b.innerText = opt;
    b.onclick = () => submitAnswer(opt, q.options[q.correct_option_index], q.question, lang);
    optBox.appendChild(b);
  });
}

async function submitAnswer(selected, correct, question, lang) {
  const formData = new FormData();
  formData.append("question", question);
  formData.append("correct_answer", correct);
  formData.append("student_answer", selected);
  formData.append("language", lang);

  const res = await fetch("http://localhost:8000/api/evaluate-response", {
    method: "POST",
    body: formData
  });
  const data = (await res.json()).feedback;

  studentPerformance.push({
    question: question,
    student_answer: selected,
    is_correct: data.is_correct
  });

  const misBox = document.getElementById("misconception-box");
  misBox.style.display = "block";
  
  document.getElementById("speech-bubble").innerText = data.teacher_remediation;
  
  // Briefly speak remediation
  synth.cancel();
  const utterance = new SpeechSynthesisUtterance(data.teacher_remediation);
  utterance.voice = teacherVoice;
  utterance.rate = 0.85; 
  utterance.onstart = () => avatarVideo.play();
  utterance.onend = () => avatarVideo.pause();
  synth.speak(utterance);

  if (data.is_correct) {
    misBox.style.background = "rgba(20, 83, 45, 0.8)";
    misBox.style.borderColor = "#22c55e";
    misBox.style.color = "#86efac";
    misBox.innerText = "Correct! " + data.teacher_remediation;
  } else {
    misBox.style.background = "rgba(63, 29, 36, 0.8)";
    misBox.style.borderColor = "#ef4444";
    misBox.style.color = "#fca5a5";
    misBox.innerText = "Needs Review:\n" + data.teacher_remediation;
  }

  const nextBtn = document.getElementById("btn-next-module");
  nextBtn.innerText = "Next Question →";
  nextBtn.style.display = "block";
  
  nextBtn.onclick = () => {
    currentQuizIndex++;
    renderQuizQuestion();
  };
}

async function generateFinalReport() {
  document.getElementById("classroom").style.display = "none";
  document.getElementById("report-panel").style.display = "block";
  synth.cancel(); 

  const formData = new FormData();
  formData.append("student_performance_data", JSON.stringify(studentPerformance));
  formData.append("topic", document.getElementById("topic-input").value || "Uploaded Document");

  try {
    const res = await fetch("http://localhost:8000/api/final-report", {
      method: "POST",
      body: formData
    });
    const result = await res.json();
    const report = result.report;

    document.getElementById("report-content").innerHTML = `
      <h3 style="color:#00e5ff;">Overall Score: ${report.score_percentage}%</h3>
      <p><strong>Mastered Concepts:</strong> ${report.concepts_understood.join(", ") || "None"}</p>
      <p><strong>Areas for Improvement:</strong> ${report.weak_areas.join(", ") || "None"}</p>
      <p><strong>Teacher's Recommendation:</strong> ${report.recommended_revision}</p>
      <br>
      <p><strong>Suggested Next Topic:</strong> ${report.suggested_next_topic}</p>
    `;
  } catch (err) {
    document.getElementById("report-content").innerHTML = "Error loading report: " + err.message;
  }
}