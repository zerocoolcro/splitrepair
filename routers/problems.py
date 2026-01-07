@router.post("/problems/create")
async def create_problem(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    filename = None

    if file:
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        file_ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = f"{upload_dir}/{filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    problem = Problem(
        title=title,
        description=description,
        category=category,
        user_id=current_user.id,
        image_url=filename
    )

    db.add(problem)
    db.commit()
    db.refresh(problem)

    return problem
