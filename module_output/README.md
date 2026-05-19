# Moodle Import Instructions

This directory contains the fully structured **Aviation Weather Forecasting Certification - Module 1**. Follow these steps to import the content and quiz into your Moodle environment.

## 1. Import the Lesson Content (HTML)

Because the lessons are visual-forward and use custom CSS, they are best imported as "Page" resources in Moodle.

1. Go to your Moodle course and click **Turn editing on**.
2. In the desired section (e.g., "Module 1"), click **Add an activity or resource** and select **Page**.
3. Name the page according to the lesson (e.g., *Lesson 1: International Regulatory Frameworks*).
4. In the **Content** section, click the **Show more buttons** icon (the down arrow) in the text editor, then click the **HTML `</>`** button to switch to code view.
5. Open the corresponding `.html` file from `./module_output/lessons/` in a text editor (e.g., Notepad or VS Code). Copy the entire content and paste it into the Moodle HTML view.
6. Click **Save and return to course**.
7. Repeat this process for `00_module_overview.html` and the 4 lesson HTML files.

## 2. Upload the Images

Moodle will need the images referenced in the HTML files.

1. Ensure you have sourced the images listed in `IMAGES_TO_SOURCE.md` and saved them.
2. In Moodle, you can upload these images directly to the course files or host them externally. 
3. If uploading to Moodle: go back into the Page settings for each lesson, click the **Image** button in the text editor toolbar, upload the specific image, and insert it to replace the `<figure>` placeholder block if necessary. *(Alternatively, if hosting externally, simply update the `src=""` attribute in the HTML code to point to your hosted URL).*

## 3. Import the Quiz Questions (XML)

The quiz questions have been prepared in Moodle XML format, which allows for bulk importing of questions, correct answers, and feedback rationales.

1. In your Moodle course, click the **Settings (gear) icon** and select **More...**
2. Scroll down to the **Question bank** section and click **Import**.
3. For the **File format**, select **Moodle XML format**.
4. In the **General** section, you may choose to import them into a specific category (e.g., "Module 1 Questions").
5. Drag and drop the `./module_output/module_quiz_all_questions.xml` file into the upload box (or use the file picker).
6. Click **Import**. Moodle will display a preview of the imported questions. Click **Continue**.

## 4. Create the Final Quiz Activity

1. Return to your course page and click **Add an activity or resource**, then select **Quiz**.
2. Name it "Module 1 Certification Quiz".
3. Under **Grade**, set the **Grade to pass** to reflect the 75% requirement (e.g., 7.5 out of 10, or 12 out of 16 depending on your total point scaling).
4. Save the quiz settings.
5. Click on the newly created quiz and select **Edit quiz**.
6. Click **Add** -> **from question bank** and select all the imported questions from the "Module 1 Questions" category.
7. Set the **Maximum grade** to match your course structure and click **Save**.

Your Module 1 is now fully integrated and ready for students!
